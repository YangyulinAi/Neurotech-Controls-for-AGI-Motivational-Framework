"""
Real-time EEG streaming with LSL auto-reconnection and resampling to 256 Hz
Enhanced for multi-device support (Muse2, X.on, OpenBCI Cyton, Standard 10-20)
"""
import time
import numpy as np
import mne
from pylsl import resolve_stream, StreamInlet, LostError
import logging

# Configure logging
logger = logging.getLogger(__name__)

def connect_eeg_stream(timeout: int = 5, stream_type: str = 'EEG') -> StreamInlet:
    """
    Connect to EEG stream with automatic retry
    
    Args:
        timeout: Timeout for stream resolution
        stream_type: LSL stream type to look for
        
    Returns:
        StreamInlet object for the connected stream
    """
    while True:
        try:
            logger.info(f"Searching for {stream_type} streams...")
            streams = resolve_stream('type', stream_type, timeout)
            
            if streams:
                inlet = StreamInlet(streams[0], max_buflen=60)  # 60 second buffer
                stream_info = streams[0]
                
                logger.info(f"[LSL] Connected to: {stream_info.name()}")
                logger.info(f"[LSL] Channels: {stream_info.channel_count()}")
                logger.info(f"[LSL] Sampling rate: {stream_info.nominal_srate()} Hz")
                logger.info(f"[LSL] Source ID: {stream_info.source_id()}")
                
                return inlet
            else:
                logger.warning(f"[LSL] No {stream_type} streams found, retrying...")
                
        except Exception as e:
            logger.error(f"[LSL] Stream connection error: {e}")
            
        time.sleep(1)

def pull_and_resample(inlet: StreamInlet, target_fs: int = 256, max_samples: int = 1000) -> np.ndarray:
    """
    Pull data from LSL stream and resample to target frequency
    
    Args:
        inlet: LSL StreamInlet object
        target_fs: Target sampling rate (Hz)
        max_samples: Maximum samples to pull at once
        
    Returns:
        Resampled EEG data as numpy array (channels × timepoints)
        Returns None if no data available
    """
    try:
        # Pull chunk of samples with timestamps
        samples, timestamps = inlet.pull_chunk(timeout=0.5, max_samples=max_samples)
        
        if not timestamps:
            return None
            
        # Convert to numpy arrays
        X = np.asarray(samples, dtype=float).T  # channels × timepoints
        t = np.asarray(timestamps, dtype=float)
        
        logger.debug(f"[LSL] Pulled {len(samples)} samples, {X.shape[0]} channels")
        
        # Estimate sampling rate from timestamps if enough data
        if len(t) > 3:
            dt = np.diff(t)
            good_intervals = np.isfinite(dt) & (dt > 0)
            
            if good_intervals.any():
                estimated_fs = int(round(1 / np.median(dt[good_intervals])))
            else:
                estimated_fs = target_fs
        else:
            estimated_fs = target_fs
            
        # Resample if necessary
        if estimated_fs != target_fs and len(t) > 1:
            logger.debug(f"[LSL] Resampling from {estimated_fs} Hz to {target_fs} Hz")
            
            # Create MNE Raw object for resampling
            ch_names = [f"CH{i+1}" for i in range(X.shape[0])]
            info = mne.create_info(ch_names, estimated_fs, "eeg")
            raw = mne.io.RawArray(X, info, verbose=False)
            
            # Resample using MNE
            raw = raw.resample(target_fs, verbose=False)
            X = raw.get_data()
            
        # Clean invalid values
        X[~np.isfinite(X)] = 0.0
        
        logger.debug(f"[LSL] Final data shape: {X.shape}")
        return X
        
    except LostError:
        logger.warning("[LSL] Stream connection lost")
        return None
    except Exception as e:
        logger.error(f"[LSL] Data processing error: {e}")
        return None

def monitor_stream_quality(inlet: StreamInlet, duration: float = 10.0) -> dict:
    """
    Monitor stream quality metrics
    
    Args:
        inlet: LSL StreamInlet object
        duration: Duration to monitor (seconds)
        
    Returns:
        Dictionary with quality metrics
    """
    logger.info(f"[LSL] Monitoring stream quality for {duration} seconds...")
    
    start_time = time.time()
    total_samples = 0
    dropped_samples = 0
    timestamps = []
    
    while time.time() - start_time < duration:
        try:
            samples, ts = inlet.pull_chunk(timeout=1.0)
            
            if ts:
                total_samples += len(samples)
                timestamps.extend(ts)
                
                # Check for dropped samples (large timestamp gaps)
                if len(timestamps) > 1:
                    dt = np.diff(timestamps[-10:])  # Check last 10 intervals
                    expected_dt = 1.0 / inlet.info().nominal_srate()
                    dropped = np.sum(dt > expected_dt * 2)  # Gaps > 2x expected
                    dropped_samples += dropped
                    
        except Exception as e:
            logger.error(f"[LSL] Quality monitoring error: {e}")
            break
            
        time.sleep(0.1)
    
    # Calculate metrics
    duration_actual = time.time() - start_time
    sample_rate = total_samples / duration_actual if duration_actual > 0 else 0
    drop_rate = dropped_samples / total_samples if total_samples > 0 else 0
    
    quality = {
        "duration": duration_actual,
        "total_samples": total_samples,
        "dropped_samples": dropped_samples,
        "sample_rate": sample_rate,
        "drop_rate": drop_rate,
        "quality_score": max(0, 1 - drop_rate)  # 0-1 score
    }
    
    logger.info(f"[LSL] Quality metrics: {quality}")
    return quality

class LSLStreamer:
    """
    High-level LSL streaming interface with auto-reconnection
    """
    
    def __init__(self, target_fs: int = 256, stream_type: str = 'EEG'):
        """
        Initialize LSL streamer
        
        Args:
            target_fs: Target sampling rate
            stream_type: LSL stream type to connect to
        """
        self.target_fs = target_fs
        self.stream_type = stream_type
        self.inlet = None
        self.is_connected = False
        self.last_data_time = 0
        
    def connect(self) -> bool:
        """
        Connect to LSL stream
        
        Returns:
            True if connection successful
        """
        try:
            self.inlet = connect_eeg_stream(stream_type=self.stream_type)
            self.is_connected = True
            self.last_data_time = time.time()
            logger.info("[LSL] Streamer connected successfully")
            return True
        except Exception as e:
            logger.error(f"[LSL] Connection failed: {e}")
            self.is_connected = False
            return False
    
    def get_data(self) -> np.ndarray:
        """
        Get resampled data from stream
        
        Returns:
            EEG data array or None if no data/connection lost
        """
        if not self.is_connected:
            if not self.connect():
                return None
                
        try:
            data = pull_and_resample(self.inlet, self.target_fs)
            
            if data is not None:
                self.last_data_time = time.time()
                return data
            else:
                # Check for connection timeout
                if time.time() - self.last_data_time > 5.0:  # 5 second timeout
                    logger.warning("[LSL] Connection timeout - attempting reconnect")
                    self.is_connected = False
                    
                return None
                
        except Exception as e:
            logger.error(f"[LSL] Data retrieval error: {e}")
            self.is_connected = False
            return None
    
    def disconnect(self):
        """Disconnect from stream"""
        if self.inlet:
            try:
                del self.inlet
            except:
                pass
            self.inlet = None
            
        self.is_connected = False
        logger.info("[LSL] Streamer disconnected")
    
    def get_status(self) -> dict:
        """Get current status"""
        return {
            "connected": self.is_connected,
            "target_fs": self.target_fs,
            "stream_type": self.stream_type,
            "last_data_time": self.last_data_time
        }


# Example usage for real-time processing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create streamer
    streamer = LSLStreamer(target_fs=256)
    
    # Connect and stream
    if streamer.connect():
        logger.info("Starting real-time data streaming...")
        
        try:
            while True:
                data = streamer.get_data()
                
                if data is not None:
                    logger.info(f"Received data: {data.shape} at {time.time():.2f}")
                    
                    # Your real-time processing pipeline would go here
                    # e.g., preprocessing → feature extraction → ONNX inference → broadcast
                    
                time.sleep(0.1)  # 100ms processing cycle
                
        except KeyboardInterrupt:
            logger.info("Stopping stream...")
        finally:
            streamer.disconnect()
    else:
        logger.error("Failed to connect to LSL stream")