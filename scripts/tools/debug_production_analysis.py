#!/usr/bin/env python3
"""
Debug script to test analysis environment in production
"""
import sys
import os
import json
import requests
from pathlib import Path

def test_environment():
    print("=== Production Environment Test ===")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    
    # Test if we can import required modules
    try:
        import numpy as np
        print(f"NumPy version: {np.__version__}")
    except ImportError as e:
        print(f"NumPy import failed: {e}")
    
    try:
        import scipy
        print(f"SciPy version: {scipy.__version__}")
    except ImportError as e:
        print(f"SciPy import failed: {e}")
    
    try:
        import onnxruntime as ort
        print(f"ONNX Runtime version: {ort.__version__}")
    except ImportError as e:
        print(f"ONNX Runtime import failed: {e}")
    
    # Test if we can find the analysis scripts
    old_script_path = "tests/analyze_set_file_onnx.py"
    new_script_path = "tests/analyze_file_onnx.py"
    
    if os.path.exists(old_script_path):
        print(f"Legacy analysis script found: {old_script_path}")
    else:
        print(f"Legacy analysis script NOT found: {old_script_path}")
    
    if os.path.exists(new_script_path):
        print(f"New unified analysis script found: {new_script_path}")
    else:
        print(f"New unified analysis script NOT found: {new_script_path}")
    
    # Test if we can find the ONNX model
    model_path = "model/va_regressor.onnx"
    if os.path.exists(model_path):
        print(f"ONNX model found: {model_path}")
    else:
        print(f"ONNX model NOT found: {model_path}")
    
    # Test if we can find data files
    data_dir = "data/training set/s2"
    if os.path.exists(data_dir):
        files = list(Path(data_dir).glob("*.set"))
        print(f"Found {len(files)} SET files in {data_dir}")
        if files:
            print(f"Sample file: {files[0]}")
    else:
        print(f"Data directory NOT found: {data_dir}")

def test_api_connection():
    print("\n=== API Connection Test ===")
    try:
        response = requests.post('http://localhost:5000/api/bci/broadcast', 
                               json={
                                   "valence": -0.1,
                                   "arousal": 0.2,
                                   "phi": 0.05,
                                   "type": "bci_data",
                                   "timestamp": 1.0
                               },
                               timeout=5)
        print(f"API broadcast test: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"API connection failed: {e}")

if __name__ == "__main__":
    test_environment()
    test_api_connection()