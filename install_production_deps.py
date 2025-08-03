#!/usr/bin/env python3
"""
Install missing production dependencies
"""
import subprocess
import sys
import os

def install_package(package):
    """Install a Python package using pip"""
    try:
        print(f"Installing {package}...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", package
        ], capture_output=True, text=True, check=True)
        print(f"✓ {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install {package}")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("=== Installing Production Dependencies ===")
    
    # Required packages for production
    packages = [
        "onnxruntime",
        "requests",  # For API calls
    ]
    
    success_count = 0
    for package in packages:
        if install_package(package):
            success_count += 1
    
    print(f"\n=== Installation Summary ===")
    print(f"Packages installed: {success_count}/{len(packages)}")
    
    # Test imports
    print("\n=== Testing Imports ===")
    try:
        import onnxruntime as ort
        print(f"✓ ONNX Runtime {ort.__version__} imported successfully")
    except ImportError as e:
        print(f"✗ ONNX Runtime import failed: {e}")
    
    try:
        import requests
        print(f"✓ Requests imported successfully")
    except ImportError as e:
        print(f"✗ Requests import failed: {e}")

if __name__ == "__main__":
    main()