#!/usr/bin/env python3
"""
Production Environment Diagnostic Script
Checks all dependencies and paths needed for BCI analysis
"""

import sys
import os
import importlib.util
from pathlib import Path

def check_python_modules():
    """Check if required Python modules are available"""
    print("=== Python Module Check ===")
    required_modules = [
        'numpy', 'scipy', 'torch', 'onnxruntime', 
        'requests', 'json', 'time'
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module}: Available")
        except ImportError:
            print(f"✗ {module}: Missing")
    print()

def check_file_paths():
    """Check if required files exist"""
    print("=== File Path Check ===")
    
    # Get current working directory
    cwd = os.getcwd()
    print(f"Current directory: {cwd}")
    
    required_files = [
        'tests/analyze_set_file_onnx.py',
        'model/va_regressor.onnx',
        'src/preprocess.py',
        'src/onnx_runner.py',
        'src/phi_estimator.py',
        'data/training set'
    ]
    
    for file_path in required_files:
        full_path = os.path.join(cwd, file_path)
        if os.path.exists(full_path):
            print(f"✓ {file_path}: Exists")
        else:
            print(f"✗ {file_path}: Missing")
    print()

def check_demo_data():
    """Check if demo data files exist"""
    print("=== Demo Data Check ===")
    
    data_dir = 'data/training set'
    if os.path.exists(data_dir):
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                if file.endswith('.set'):
                    print(f"✓ Found SET file: {os.path.join(root, file)}")
    else:
        print(f"✗ Data directory not found: {data_dir}")
    print()

def check_src_imports():
    """Test importing src modules"""
    print("=== Source Module Import Check ===")
    
    src_path = os.path.join(os.getcwd(), 'src')
    sys.path.insert(0, src_path)
    
    modules_to_test = [
        ('preprocess.py', 'Preprocessor'),
        ('onnx_runner.py', 'ONNXRunner'),
        ('phi_estimator.py', 'PhiEstimator')
    ]
    
    for module_file, class_name in modules_to_test:
        try:
            module_path = os.path.join(src_path, module_file)
            spec = importlib.util.spec_from_file_location(f"src_{module_file[:-3]}", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, class_name):
                print(f"✓ {module_file}: {class_name} class available")
            else:
                print(f"✗ {module_file}: {class_name} class not found")
                
        except Exception as e:
            print(f"✗ {module_file}: Import failed - {e}")
    print()

def check_environment():
    """Check environment variables and settings"""
    print("=== Environment Check ===")
    
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    print(f"NODE_ENV: {os.environ.get('NODE_ENV', 'Not set')}")
    print()

if __name__ == '__main__':
    print("BCI Production Environment Diagnostic")
    print("=====================================")
    
    check_environment()
    check_python_modules()
    check_file_paths()
    check_demo_data()
    check_src_imports()
    
    print("Diagnostic complete!")