#!/usr/bin/env python3
"""
Production Environment Validation Tool
Checks all required dependencies and system configuration for Neural Axis deployment
"""
import sys
import json
import subprocess
from pathlib import Path

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        return {"status": "ok", "version": f"{version.major}.{version.minor}.{version.micro}"}
    else:
        return {"status": "error", "version": f"{version.major}.{version.minor}.{version.micro}", 
                "message": "Python 3.8+ required"}

def check_dependencies():
    """Check all required Python dependencies"""
    required = [
        "numpy", "scipy", "mne", "pandas", 
        "onnxruntime", "pylsl", "requests", 
        "websockets", "h5py", "pyedflib"
    ]
    
    results = {}
    missing = []
    
    for module in required:
        try:
            # Import and get version if possible
            mod = __import__(module)
            version = getattr(mod, '__version__', 'unknown')
            results[module] = {"status": "ok", "version": version}
        except ImportError as e:
            results[module] = {"status": "missing", "error": str(e)}
            missing.append(module)
        except Exception as e:
            results[module] = {"status": "error", "error": str(e)}
            missing.append(module)
    
    return results, missing

def check_onnx_providers():
    """Check available ONNX Runtime providers"""
    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        
        gpu_available = any(p in providers for p in ["CUDAExecutionProvider", "ROCMExecutionProvider"])
        
        return {
            "status": "ok",
            "providers": providers,
            "gpu_support": gpu_available,
            "cpu_support": "CPUExecutionProvider" in providers
        }
    except ImportError:
        return {"status": "missing", "message": "onnxruntime not installed"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def check_model_files():
    """Check for required model files"""
    model_dir = Path("model")
    required_files = ["va_regressor.onnx"]
    
    results = {}
    for filename in required_files:
        filepath = model_dir / filename
        if filepath.exists():
            size_mb = filepath.stat().st_size / (1024 * 1024)
            results[filename] = {"status": "ok", "size_mb": round(size_mb, 2)}
        else:
            results[filename] = {"status": "missing", "path": str(filepath)}
    
    return results

def check_data_directories():
    """Check for required data directories"""
    directories = [
        "data/training set",
        "model",
        "src", 
        "tests"
    ]
    
    results = {}
    for dirname in directories:
        dirpath = Path(dirname)
        if dirpath.exists() and dirpath.is_dir():
            file_count = len(list(dirpath.rglob("*")))
            results[dirname] = {"status": "ok", "files": file_count}
        else:
            results[dirname] = {"status": "missing", "path": str(dirpath)}
    
    return results

def check_lsl_environment():
    """Check LSL (Lab Streaming Layer) configuration"""
    try:
        import pylsl
        
        # Test basic LSL functionality
        info = pylsl.StreamInfo("test", "Marker", 1, 0, "float32", "test123")
        outlet = pylsl.StreamOutlet(info)
        
        # Clean up
        del outlet
        del info
        
        return {
            "status": "ok",
            "version": getattr(pylsl, '__version__', 'unknown'),
            "test": "passed"
        }
    except ImportError:
        return {"status": "missing", "message": "pylsl not installed"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def check_system_resources():
    """Check system resources"""
    import psutil
    
    cpu_count = psutil.cpu_count(logical=True)
    memory_gb = psutil.virtual_memory().total / (1024**3)
    disk_gb = psutil.disk_usage('.').free / (1024**3)
    
    return {
        "cpu_cores": cpu_count,
        "memory_gb": round(memory_gb, 1),
        "disk_free_gb": round(disk_gb, 1),
        "recommendations": {
            "cpu": "ok" if cpu_count >= 4 else "warning: recommend 4+ cores",
            "memory": "ok" if memory_gb >= 8 else "warning: recommend 8+ GB RAM",
            "disk": "ok" if disk_gb >= 5 else "warning: recommend 5+ GB free space"
        }
    }

def main():
    """Run all production environment checks"""
    print("Neural Axis Production Environment Check")
    print("=" * 40)
    
    # Collect all check results
    results = {
        "python": check_python_version(),
        "dependencies": check_dependencies(),
        "onnx": check_onnx_providers(),
        "models": check_model_files(),
        "directories": check_data_directories(),
        "lsl": check_lsl_environment(),
        "system": check_system_resources()
    }
    
    # Determine overall status
    overall_status = "ok"
    issues = []
    
    # Check for critical issues
    if results["python"]["status"] != "ok":
        overall_status = "error"
        issues.append("Python version incompatible")
    
    _, missing_deps = results["dependencies"]
    if missing_deps:
        overall_status = "error"
        issues.append(f"Missing dependencies: {', '.join(missing_deps)}")
    
    if results["onnx"]["status"] != "ok":
        overall_status = "error"
        issues.append("ONNX Runtime not available")
    
    # Check for warnings
    model_missing = [k for k, v in results["models"].items() if v["status"] != "ok"]
    if model_missing:
        if overall_status == "ok":
            overall_status = "warning"
        issues.append(f"Missing model files: {', '.join(model_missing)}")
    
    # Final results
    results["overall"] = {
        "status": overall_status,
        "issues": issues,
        "ready_for_production": overall_status == "ok"
    }
    
    # Output results
    print(json.dumps(results, indent=2))
    
    # Exit with appropriate code
    if overall_status == "error":
        sys.exit(1)
    elif overall_status == "warning":
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCheck interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Check failed with error: {e}")
        sys.exit(1)