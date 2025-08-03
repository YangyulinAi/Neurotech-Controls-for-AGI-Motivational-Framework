#!/usr/bin/env python3
"""
Analyze EEG SET file using proper preprocessing and ONNX model inference
"""
import sys
import os
import numpy as np
import scipy.io
import json
import requests
import time
from pathlib import Path

# Add src directory to path (now we're in tests/, need to go up one level)
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_path)

try:
    # Import with absolute module names to avoid conflicts
    import importlib.util
    
    # Load preprocess module
    preprocess_spec = importlib.util.spec_from_file_location("src_preprocess", os.path.join(src_path, "preprocess.py"))
    preprocess_module = importlib.util.module_from_spec(preprocess_spec)
    preprocess_spec.loader.exec_module(preprocess_module)
    
    # Load onnx_runner module  
    onnx_spec = importlib.util.spec_from_file_location("src_onnx_runner", os.path.join(src_path, "onnx_runner.py"))
    onnx_module = importlib.util.module_from_spec(onnx_spec)
    onnx_spec.loader.exec_module(onnx_module)
    
    # Extract classes
    Preprocessor = preprocess_module.Preprocessor
    extract_feats = preprocess_module.extract_feats
    ONNXRunner = onnx_module.ONNXRunner
    
    print("Successfully loaded preprocessing and ONNX modules")
    
except Exception as e:
    print(f"Error importing modules: {e}")
    print("Make sure src/preprocess.py and src/onnx_runner.py exist")
    sys.exit(1)

def load_set_file(filepath):
    """Load EEGLAB .set file"""
    try:
        mat_data = scipy.io.loadmat(filepath, struct_as_record=False, squeeze_me=True)
        
        # Extract EEG data
        if 'data' in mat_data:
            data = mat_data['data']
        else:
            # Look for data in nested structure
            for key, value in mat_data.items():
                if hasattr(value, 'shape') and len(value.shape) == 2:
                    data = value
                    break
            else:
                raise ValueError("Could not find EEG data in SET file")
        
        # Ensure correct orientation (channels x time)
        if data.shape[0] > data.shape[1]:
            data = data.T
            
        return data
        
    except Exception as e:
        print(f"Error loading SET file: {e}")
        return None

def send_to_websocket(valence, arousal, timestamp, phi=None):
    """Send prediction to WebSocket via REST API"""
    try:
        data = {
            'valence': float(valence),
            'arousal': float(arousal),
            'timestamp': timestamp,
            'type': 'bci_data'
        }
        if phi is not None:
            data['phi'] = float(phi)
        
        response = requests.post('http://localhost:5000/api/bci/broadcast', 
                               json=data, 
                               timeout=1)
        
        if response.status_code == 200:
            if phi is not None:
                print(f"Sent to WebSocket: V={valence:.3f}, A={arousal:.3f}, Φ={phi:.4f}")
            else:
                print(f"Sent to WebSocket: V={valence:.3f}, A={arousal:.3f}")
        else:
            print(f"Failed to send to WebSocket: {response.status_code}")
            
    except Exception as e:
        print(f"WebSocket send error: {e}")

def analyze_set_file_with_onnx(filepath, model_path='model/va_regressor.onnx', compute_phi=False, phi_method='mock'):
    """Analyze SET file using proper preprocessing and ONNX model"""
    
    print(f"Loading ONNX model: {model_path}")
    if not os.path.exists(model_path):
        print(f"Error: ONNX model not found at {model_path}")
        return None
    
    # Initialize ONNX runner
    try:
        onnx_runner = ONNXRunner(model_path)
        print("ONNX model loaded successfully")
    except Exception as e:
        print(f"Error loading ONNX model: {e}")
        return None
    
    # Load SET file
    print(f"Loading SET file: {filepath}")
    data = load_set_file(filepath)
    if data is None:
        return None
    
    n_channels, n_samples = data.shape
    print(f"Loaded EEG data: {n_channels} channels, {n_samples} samples")
    
    # Initialize preprocessor (1-45 Hz bandpass)
    fs = 256  # Sampling frequency
    preprocessor = Preprocessor(fs, 1, 45)
    
    # Create 5-second windows (1280 samples at 256 Hz)
    window_size = int(5 * fs)
    step_size = int(1.25 * fs)  # 1.25s step (overlap)
    
    predictions = []
    
    for i in range(0, n_samples - window_size + 1, step_size):
        start_idx = i
        end_idx = i + window_size
        
        # Extract window (channels x time)
        window = data[:, start_idx:end_idx]
        
        # Preprocess the window
        try:
            # Transpose for preprocessor (time x channels)
            window_t = window.T
            preprocessed = preprocessor.transform(window_t)
            # Transpose back (channels x time)
            preprocessed = preprocessed.T
            
            # Extract features for ONNX model
            spec3, de_vec = extract_feats(preprocessed, fs)
            
            # Prepare inputs for ONNX (add batch dimension)
            spec_input = spec3[np.newaxis, ...]  # (1, 3, 224, 224)
            de_input = de_vec[np.newaxis, ...]   # (1, 26)
            
            # Run ONNX inference
            output = onnx_runner.predict(spec_input, de_input)
            valence, arousal = output[0]  # Extract from batch
            
            # Calculate timestamp
            timestamp_sec = start_idx / fs
            
            # Compute Φ if requested
            phi_value = None
            if compute_phi:
                try:
                    from src.phi_estimator import PhiEstimator
                    phi_estimator = PhiEstimator(method=phi_method)
                    phi_value = phi_estimator.estimate_phi(preprocessed[:8])  # First 8 channels
                    print(f"Window {len(predictions)+1} (t={timestamp_sec:.1f}s): Valence={valence:.3f}, Arousal={arousal:.3f}, Φ={phi_value:.4f}")
                except Exception as e:
                    print(f"Window {len(predictions)+1} (t={timestamp_sec:.1f}s): Valence={valence:.3f}, Arousal={arousal:.3f}, Φ=error({e})")
                    phi_value = 0.0
            else:
                print(f"Window {len(predictions)+1} (t={timestamp_sec:.1f}s): Valence={valence:.3f}, Arousal={arousal:.3f}")
            
            # Store prediction
            prediction = {
                'valence': float(valence),
                'arousal': float(arousal),
                'timestamp': float(timestamp_sec)
            }
            if phi_value is not None:
                prediction['phi'] = float(phi_value)
            predictions.append(prediction)
            
            # Send to WebSocket in real-time (always include phi_value, even if None/0.0)
            send_to_websocket(valence, arousal, timestamp_sec, phi_value if phi_value is not None else 0.0)
            
            # Small delay to simulate real-time processing
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Error processing window {len(predictions)+1}: {e}")
            continue
    
    return predictions

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_set_file_onnx.py <set_file_path> [model_path] [--compute_phi] [--method mock]")
        sys.exit(1)
    
    set_file = sys.argv[1]
    model_path = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else 'model/va_regressor.onnx'
    
    # Parse additional arguments
    compute_phi = '--compute_phi' in sys.argv
    phi_method = 'mock'  # Default method
    if '--method' in sys.argv:
        method_idx = sys.argv.index('--method') + 1
        if method_idx < len(sys.argv):
            phi_method = sys.argv[method_idx]
    
    print(f"DEBUG: Python script started")
    print(f"DEBUG: Arguments received: {sys.argv}")
    print(f"DEBUG: Analyzing SET file: {set_file}")
    print(f"DEBUG: Using ONNX model: {model_path}")
    print(f"DEBUG: Current working directory: {os.getcwd()}")
    
    # Flush output immediately
    sys.stdout.flush()
    
    # Check if files exist
    if not os.path.exists(set_file):
        print(f"Error: SET file not found: {set_file}")
        sys.exit(1)
    
    if not os.path.exists(model_path):
        print(f"Error: ONNX model not found: {model_path}")
        sys.exit(1)
    
    # Run analysis with ONNX model
    print("\nStarting Real-Time EEG Emotion Analysis:")
    print("=" * 50)
    
    predictions = analyze_set_file_with_onnx(set_file, model_path, compute_phi, phi_method)
    
    if predictions is None or len(predictions) == 0:
        print("No predictions generated - analysis failed")
        sys.exit(1)
    
    # Calculate summary statistics
    avg_valence = np.mean([p['valence'] for p in predictions])
    avg_arousal = np.mean([p['arousal'] for p in predictions])
    
    print("\nAnalysis Summary:")
    print("=" * 30)
    print(f"Total Windows Processed: {len(predictions)}")
    print(f"Average Valence: {avg_valence:.3f}")
    print(f"Average Arousal: {avg_arousal:.3f}")
    
    # Save results to JSON
    output_file = set_file.replace('.set', '_onnx_analysis.json')
    results = {
        'file': set_file,
        'model': model_path,
        'summary': {
            'avg_valence': avg_valence,
            'avg_arousal': avg_arousal,
            'total_windows': len(predictions)
        },
        'predictions': predictions
    }
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Detailed results saved to: {output_file}")
    
    # Send completion notification
    print("ANALYSIS_COMPLETE: Real-time ONNX analysis finished successfully")
    sys.stdout.flush()

if __name__ == '__main__':
    main()