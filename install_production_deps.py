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
        "numpy",
        "scipy", 
        "mne",  # MNE-Python for EEG data
        "pandas",  # For CSV data handling
        "onnxruntime",
        "pylsl",  # Lab Streaming Layer
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
    import_tests = [
        ("numpy", "np", "__version__"),
        ("scipy", "scipy", "__version__"),
        ("mne", "mne", "__version__"),
        ("pandas", "pd", "__version__"),
        ("onnxruntime", "ort", "__version__"),
        ("pylsl", "pylsl", "version"),
        ("requests", "requests", "__version__"),
    ]
    
    for module_name, import_as, version_attr in import_tests:
        try:
            module = __import__(module_name)
            if hasattr(module, version_attr):
                version = getattr(module, version_attr)
                print(f"✓ {module_name} {version} imported successfully")
            else:
                print(f"✓ {module_name} imported successfully")
        except ImportError as e:
            print(f"✗ {module_name} import failed: {e}")
        except RuntimeError as e:
            if module_name == "pylsl" and "LSL binary library" in str(e):
                print(f"⚠ {module_name} requires liblsl binary - install with: conda install -c conda-forge liblsl")
            else:
                print(f"✗ {module_name} runtime error: {e}")
        except Exception as e:
            print(f"✗ {module_name} unexpected error: {e}")
    
    print("\n=== LSL Library Notice ===")
    print("For real-time EEG streaming, install liblsl binary:")
    print("  conda install -c conda-forge liblsl")
    print("Or download from: https://github.com/sccn/liblsl/releases")

if __name__ == "__main__":
    main()