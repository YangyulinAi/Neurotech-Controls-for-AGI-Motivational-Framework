#!/usr/bin/env python3
"""
SET File Real Data Analyzer for Neurotech Controls for AGI Motivational Framework
Loads .set files, processes them through the actual ML pipeline, and sends predictions via WebSocket
Developed by Neural Axis
"""

import asyncio
import websockets
import json
import numpy as np
import sys
import os
from datetime import datetime
import scipy.io
import requests

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.onnx_runner import ONNXRunner
from src.preprocess import extract_feats

class SETFileAnalyzer:
    def __init__(self, set_file_path, websocket_url="ws://localhost:5000/ws"):
        self.set_file_path = set_file_path
        self.websocket_url = websocket_url
        self.websocket = None
        self.data = None
        self.running = True
        
        # Initialize ONNX model
        model_path = 'model/va_regressor.onnx'
        self.onnx_runner = ONNXRunner(model_path)
        print(f"Loaded ONNX model from {model_path}")

    def resize_spectrogram(self, spec_data, target_size=(224, 224)):
        """
        Resize spectrogram to match ONNX model input requirements
        Args:
            spec_data: np.ndarray with shape (1, 3, H, W)
            target_size: tuple (target_height, target_width)
        Returns:
            np.ndarray with shape (1, 3, target_height, target_width)
        """
        from scipy.ndimage import zoom
        
        if len(spec_data.shape) != 4:
            raise ValueError(f"Expected 4D input, got shape {spec_data.shape}")
        
        batch_size, channels, height, width = spec_data.shape
        target_height, target_width = target_size
        
        # Calculate zoom factors for height and width
        zoom_h = target_height / height
        zoom_w = target_width / width
        
        # Resize each sample and channel
        resized_data = np.zeros((batch_size, channels, target_height, target_width), dtype=np.float32)
        
        for b in range(batch_size):
            for c in range(channels):
                resized_data[b, c] = zoom(spec_data[b, c], (zoom_h, zoom_w), order=1)
        
        return resized_data

    def load_set_data(self):
        """Load EEG data from .set file for ML processing"""
        try:
            print(f"Loading SET file: {self.set_file_path}")
            
            # Load .set file (MATLAB format)
            mat_data = scipy.io.loadmat(self.set_file_path)
            
            # Extract EEG data - try common field names
            eeg_data = None
            possible_keys = ['EEG', 'data', 'eeg', 'signal']
            
            for key in possible_keys:
                if key in mat_data and hasattr(mat_data[key], 'shape'):
                    eeg_data = mat_data[key]
                    break
                elif key in mat_data and isinstance(mat_data[key], np.ndarray):
                    if mat_data[key].ndim == 2:
                        eeg_data = mat_data[key]
                        break
                elif key in mat_data and hasattr(mat_data[key][0, 0], 'data'):
                    # Handle EEGLAB structure format
                    eeg_data = mat_data[key][0, 0].data
                    break
            
            if eeg_data is None:
                print("Available keys in SET file:", list(mat_data.keys()))
                # Try to find the largest 2D array
                for key, value in mat_data.items():
                    if isinstance(value, np.ndarray) and value.ndim == 2:
                        print(f"Found 2D array '{key}' with shape {value.shape}")
                        if eeg_data is None or value.size > eeg_data.size:
                            eeg_data = value
                
                if eeg_data is None:
                    raise ValueError("Could not find EEG data in SET file")
            
            print(f"EEG data shape: {eeg_data.shape}")
            
            # Ensure data is in the correct format (channels x time)
            if eeg_data.shape[0] > eeg_data.shape[1]:
                eeg_data = eeg_data.T
                print(f"Transposed data to shape: {eeg_data.shape}")
            
            # Process EEG data into windows for analysis
            fs = 256  # Assume 256 Hz sampling rate
            window_size = 5.0  # 5 second windows
            overlap = 0.5  # 50% overlap
            
            n_channels, n_times = eeg_data.shape
            window_samples = int(window_size * fs)
            step_samples = int(window_samples * (1 - overlap))
            
            # Create windows
            n_windows = (n_times - window_samples) // step_samples + 1
            
            print(f"Creating {n_windows} windows of {window_size}s each")
            
            spec_list = []
            de_list = []
            
            for i in range(min(n_windows, 50)):  # Limit to 50 windows for reasonable processing time
                start_idx = i * step_samples
                end_idx = start_idx + window_samples
                
                if end_idx > n_times:
                    break
                
                window_data = eeg_data[:, start_idx:end_idx]
                
                # Extract features for this window
                try:
                    spec, de = extract_feats(window_data, fs)
                    spec_list.append(spec)
                    de_list.append(de)
                except Exception as e:
                    print(f"Warning: Failed to extract features for window {i}: {e}")
                    continue
            
            if len(spec_list) == 0:
                raise ValueError("No valid windows could be processed")
            
            # Stack all windows
            spec_data = np.stack(spec_list, axis=0)  # Shape: (n_windows, 3, H, W)
            de_data = np.stack(de_list, axis=0)      # Shape: (n_windows, 26)
            
            print(f"Processed {len(spec_list)} windows successfully")
            print(f"Spec data shape: {spec_data.shape}")
            print(f"DE data shape: {de_data.shape}")
            
            self.data = {
                'spec': spec_data,
                'de': de_data,
                'n_samples': spec_data.shape[0]
            }
            
            print(f"Successfully loaded {self.data['n_samples']} samples from SET file")
            return True
            
        except Exception as e:
            print(f"Error loading SET data: {e}")
            return False
    
    async def connect(self):
        """Connect to the frontend WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            print(f"Connected to frontend WebSocket server at {self.websocket_url}")
            return True
        except Exception as e:
            print(f"Failed to connect to WebSocket: {e}")
            return False
    
    async def send_prediction(self, valence, arousal, sample_idx):
        """Send ML prediction via HTTP POST to server for WebSocket broadcast"""
        try:
            message = {
                "valence": float(valence),
                "arousal": float(arousal),
                "timestamp": datetime.now().isoformat(),
                "source": "set_analysis",
                "sample_index": sample_idx
            }
            
            # Send to server via HTTP POST instead of WebSocket
            # Use port 5000 for consistency across all platforms
            response = requests.post('http://localhost:5000/api/bci/broadcast', json=message, timeout=5)
            
            if response.status_code == 200:
                print(f"Sent SET analysis prediction [{sample_idx+1}/{self.data['n_samples']}]: valence={valence:.3f}, arousal={arousal:.3f}")
                return True
            else:
                print(f"Failed to send prediction: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"Failed to send prediction: {e}")
            return False
    
    async def run_ml_inference(self, interval=1.0):
        """Run ML inference on SET data and stream predictions"""
        if not self.data:
            print("No data loaded for ML inference")
            return
            
        print(f"Starting ML inference on {self.data['n_samples']} samples from SET file...")
        print(f"Sending predictions every {interval} seconds")
        
        # Calculate more realistic timing based on the actual EEG data length
        # Each window represents 5 seconds of EEG data with 50% overlap
        # So we should simulate approximately 2.5 seconds per prediction to match real-time
        real_time_interval = 2.5  # seconds between predictions to match EEG window timing
        
        for i in range(self.data['n_samples']):
            if not self.running:
                break
                
            try:
                # Get features for this sample
                spec_raw = self.data['spec'][i:i+1]  # Shape: (1, 3, H, W)
                de = self.data['de'][i:i+1]          # Shape: (1, 26)
                
                # Resize spectrogram to match ONNX model input size (1, 3, 224, 224)
                spec_resized = self.resize_spectrogram(spec_raw, target_size=(224, 224))
                
                # Run ML inference through ONNX model
                prediction = self.onnx_runner.predict(spec_resized, de)
                
                # Extract and normalize valence and arousal from prediction
                raw_valence = prediction[0, 0]  # First output is valence
                raw_arousal = prediction[0, 1]  # Second output is arousal
                
                # Apply proper normalization - the model outputs are already in a reasonable range
                # Just apply tanh to ensure [-1, 1] bounds without excessive scaling
                valence = np.tanh(raw_valence * 2.0)  # Scale up slightly then normalize
                arousal = np.tanh(raw_arousal * 2.0)  # Scale up slightly then normalize
                
                # Send prediction to frontend
                success = await self.send_prediction(valence, arousal, i)
                
                if not success:
                    print("Failed to send prediction, attempting to reconnect...")
                    await self.connect()
                
                # Wait realistic time between predictions (2.5 seconds to match EEG window timing)
                await asyncio.sleep(real_time_interval)
                
            except Exception as e:
                print(f"Error during inference for sample {i}: {e}")
                continue
        
        print("SET file analysis completed")
        self.running = False
    
    async def start_analysis(self, interval=1.0):
        """Start the complete SET file analysis process"""
        try:
            print(f"Starting SET File Analyzer for file: {self.set_file_path}")
            
            # Load and process SET data
            if not self.load_set_data():
                print("Failed to load SET data")
                return
            
            # No need to connect to WebSocket - we'll use HTTP broadcast
            
            # Run ML inference
            await self.run_ml_inference(interval)
            
        except KeyboardInterrupt:
            print("Analysis interrupted by user")
        except Exception as e:
            print(f"Error during SET analysis: {e}")
        finally:
            if self.websocket:
                await self.websocket.close()
            print("SET analysis stopped")

async def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python analyze_set_file.py <set_file_path> [interval]")
        sys.exit(1)
    
    set_file_path = sys.argv[1]
    interval = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
    
    if not os.path.exists(set_file_path):
        print(f"Error: SET file not found: {set_file_path}")
        sys.exit(1)
    
    analyzer = SETFileAnalyzer(set_file_path)
    await analyzer.start_analysis(interval)

if __name__ == "__main__":
    asyncio.run(main())