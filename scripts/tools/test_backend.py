#!/usr/bin/env python3
"""
Test backend functionality directly
"""

import sys
import os
import json

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

def test_analysis_import():
    """Test importing the analysis script modules"""
    try:
        # Add scripts to path
        scripts_path = os.path.join(os.getcwd(), 'scripts')
        sys.path.insert(0, scripts_path)
        
        # Test direct imports
        from preprocess import Preprocessor, extract_feats
        from onnx_runner import ONNXRunner
        from phi_estimator import PhiEstimator
        
        print("✓ All modules imported successfully")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_model_loading():
    """Test ONNX model loading"""
    try:
        from onnx_runner import ONNXRunner
        
        model_path = 'model/model_onnx/va_regressor.onnx'
        if not os.path.exists(model_path):
            print(f"✗ Model file not found: {model_path}")
            return False
            
        runner = ONNXRunner(model_path)
        print("✓ ONNX model loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Model loading failed: {e}")
        return False

def test_phi_estimator():
    """Test Φ estimator"""
    try:
        from phi_estimator import PhiEstimator
        import torch
        
        estimator = PhiEstimator(method='mock')
        
        # Test with dummy data
        dummy_data = torch.randn(8, 100)  # 8 channels, 100 samples
        phi_value = estimator.estimate_phi(dummy_data)
        
        print(f"✓ Φ estimation successful: {phi_value}")
        return True
    except Exception as e:
        print(f"✗ Φ estimation failed: {e}")
        return False

def test_websocket_connection():
    """Test WebSocket endpoint"""
    try:
        import requests
        
        # Test the REST API endpoint
        response = requests.post('http://localhost:5000/api/bci/broadcast', 
                               json={
                                   'valence': -0.5,
                                   'arousal': 0.3,
                                   'timestamp': 100.0,
                                   'phi': 0.05
                               }, timeout=5)
        
        if response.status_code == 200:
            print("✓ WebSocket broadcast endpoint working")
            return True
        else:
            print(f"✗ WebSocket endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ WebSocket test failed: {e}")
        return False

if __name__ == '__main__':
    print("Backend Functionality Test")
    print("==========================")
    
    success = True
    
    print("1. Testing module imports...")
    success &= test_analysis_import()
    
    print("\n2. Testing ONNX model loading...")
    success &= test_model_loading()
    
    print("\n3. Testing Φ estimator...")
    success &= test_phi_estimator()
    
    print("\n4. Testing WebSocket endpoint...")
    success &= test_websocket_connection()
    
    print("\n" + "="*40)
    if success:
        print("✓ All tests passed! Backend should work correctly.")
    else:
        print("✗ Some tests failed. Check the errors above.")