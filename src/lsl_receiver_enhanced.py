# Enhanced LSL receiver with auto-reconnect and resampling
from pylsl import StreamInlet, resolve_stream
from .utils.ring_buffer import RingBuffer
import logging
import numpy as np
import time
import mne

class LSLReceiver:
    def __init__(self, sampling_rate, window_size, n_channels, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.target_sampling_rate = sampling_rate  # Target 256Hz
        self.buf_samples = int(sampling_rate * window_size * 2)
        self.ring = RingBuffer(self.buf_samples, n_channels)
        self.inlet = None
        self.current_sr = None
        self.reconnect_interval = 5  # seconds
        self.sample_buffer = []
        self.last_timestamp = None
        self.connection_status = "disconnected"
        
        # Connect to LSL stream with auto-reconnect
        self._connect_stream()

    def _connect_stream(self):
        """Connect to LSL stream with auto-reconnect capability"""
        while True:
            try:
                self.logger.info("Looking for LSL EEG streams...")
                self.connection_status = "connecting"
                streams = resolve_stream('type', 'EEG', timeout=5.0)
                
                if streams:
                    self.inlet = StreamInlet(streams[0])
                    stream_info = streams[0]
                    self.current_sr = stream_info.nominal_srate()
                    self.connection_status = "connected"
                    
                    self.logger.info(f"Connected to LSL stream: {stream_info.name()}")
                    self.logger.info(f"Stream sampling rate: {self.current_sr}Hz, target: {self.target_sampling_rate}Hz")
                    
                    if abs(self.current_sr - self.target_sampling_rate) > 1:
                        self.logger.warning(f"Sampling rate mismatch! Will resample from {self.current_sr}Hz to {self.target_sampling_rate}Hz")
                    
                    break
                else:
                    self.connection_status = "retrying"
                    self.logger.warning(f"No LSL EEG streams found. Retrying in {self.reconnect_interval}s...")
                    time.sleep(self.reconnect_interval)
                    
            except Exception as e:
                self.connection_status = "error"
                self.logger.error(f"LSL connection error: {e}. Retrying in {self.reconnect_interval}s...")
                time.sleep(self.reconnect_interval)

    def _resample_data(self, data):
        """Resample data to target sampling rate using MNE"""
        if abs(self.current_sr - self.target_sampling_rate) <= 1:
            return data  # No resampling needed
            
        try:
            # Convert to MNE format for resampling
            data_array = np.array(data).T  # Shape: (n_channels, n_samples)
            
            # Create fake MNE Raw object for resampling
            info = mne.create_info(
                ch_names=[f'EEG{i+1}' for i in range(data_array.shape[0])],
                sfreq=self.current_sr,
                ch_types='eeg'
            )
            
            raw = mne.io.RawArray(data_array, info, verbose=False)
            raw.resample(self.target_sampling_rate, verbose=False)
            
            # Convert back to original format
            resampled_data = raw.get_data().T  # Shape: (n_samples, n_channels)
            return resampled_data.tolist()
            
        except Exception as e:
            self.logger.error(f"Resampling failed: {e}. Using original data.")
            return data

    def get_status(self):
        """Get current connection status for UI display"""
        return self.connection_status

    def start(self):
        """Start LSL receiver loop with auto-reconnect and resampling"""
        self.logger.info("Starting LSL receiver loop with auto-reconnect...")
        
        while True:
            try:
                if self.inlet is None:
                    self._connect_stream()
                    continue
                
                # Pull sample with timeout
                sample, timestamp = self.inlet.pull_sample(timeout=1.0)
                
                if sample is not None:
                    self.connection_status = "streaming"
                    # Add to buffer for batch resampling
                    self.sample_buffer.append(sample)
                    
                    # Process buffer when we have enough samples (every 0.1 seconds worth)
                    buffer_size = int(self.current_sr * 0.1)  # 0.1 second worth of data
                    
                    if len(self.sample_buffer) >= buffer_size:
                        # Resample buffer and add to ring buffer
                        resampled_data = self._resample_data(self.sample_buffer)
                        
                        for resampled_sample in resampled_data:
                            self.ring.extend(np.array([resampled_sample]))
                        
                        # Clear buffer
                        self.sample_buffer = []
                
                else:
                    # No data received - connection may be lost
                    self.connection_status = "timeout"
                    self.logger.warning("LSL stream timeout. Attempting reconnection...")
                    self.inlet = None
                    time.sleep(self.reconnect_interval)
                    
            except Exception as e:
                self.connection_status = "error"
                self.logger.error(f"LSL receiver error: {e}. Reconnecting...")
                self.inlet = None
                time.sleep(self.reconnect_interval)