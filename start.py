#!/usr/bin/env python3
"""
Neurotech Controls for AGI Motivational Framework - Windows Python Startup Script
Cross-platform EEG emotion prediction system startup for Windows
Developed by Neural Axis
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def check_windows_dependencies():
    """Check Windows system dependencies"""
    print("🔍 Checking Windows system dependencies...")
    
    # 检查Node.js
    try:
        result = subprocess.run(['node', '--version'], 
                              capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print(f"✅ Node.js: {result.stdout.strip()}")
        else:
            print("❌ Node.js not installed. Please download from https://nodejs.org/")
            return False
    except Exception:
        print("❌ Node.js not installed. Please download from https://nodejs.org/")
        return False
    
    # Check npm dependencies
    if not Path('node_modules').exists():
        print("❌ npm dependencies not installed")
        print("Auto-installing npm dependencies...")
        result = subprocess.run(['npm', 'install'], shell=True)
        if result.returncode != 0:
            print("❌ npm dependencies installation failed")
            return False
        print("✅ npm dependencies installed successfully")
    else:
        print("✅ npm dependencies already installed")
    
    # Check Python dependencies
    required_packages = ['torch', 'onnx', 'onnxruntime', 'numpy', 'scipy', 'requests']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing Python packages: {missing_packages}")
        print("Auto-installing Python dependencies...")
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'python-requirements.txt'], 
                              shell=True)
        if result.returncode != 0:
            print("❌ Python dependencies installation failed")
            return False
        print("✅ Python dependencies installed successfully")
    else:
        print("✅ Python dependencies already installed")
    
    return True

def kill_windows_process():
    """Kill existing processes on Windows"""
    port = 5000
    try:
        print(f"🧹 Cleaning existing processes on port {port}...")
        
        # Use netstat to find processes using the port
        result = subprocess.run(['netstat', '-ano'], 
                              capture_output=True, text=True, shell=True)
        
        if result.stdout:
            lines = result.stdout.split('\n')
            for line in lines:
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        print(f"   Killing process PID: {pid}")
                        subprocess.run(['taskkill', '/F', '/PID', pid], 
                                     capture_output=True, shell=True)
        
        time.sleep(1)  # Wait for process to fully terminate
        
    except Exception as e:
        print(f"Error cleaning processes: {e}")

def start_windows_server():
    """Start Windows server"""
    port = 5000
    
    print("🚀 Starting Neurotech Controls for AGI Motivational Framework on Windows...")
    print(f"   Port: {port}")
    print(f"   Frontend URL: http://localhost:{port}")
    print("   Press Ctrl+C to stop service")
    print("")
    
    # Set environment variables
    env = os.environ.copy()
    env['PORT'] = str(port)
    env['NODE_ENV'] = 'development'
    
    try:
        # Start npm development server
        print("Starting development server...")
        process = subprocess.Popen(['npm', 'run', 'dev'], 
                                 env=env, shell=True)
        
        print(f"✅ Server started successfully!")
        print(f"🌐 Access in browser: http://localhost:{port}")
        print("")
        
        # Wait for user interruption
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n⏹️  Received stop signal...")
    
    except KeyboardInterrupt:
        print("\n⏹️  Stopping server...")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False
    
    finally:
        try:
            process.terminate()
            time.sleep(2)
            if process.poll() is None:
                process.kill()
            print("✅ Server stopped")
        except:
            pass
    
    return True

def main():
    """Windows main startup function"""
    print("🧠 Neurotech Controls for AGI Motivational Framework - Windows Launcher")
    print("=" * 65)
    print("🪟 Windows System - Port 5000 | Neural Axis")
    print("")
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help':
            print("Usage:")
            print("  python start-python-windows.py        # Start system")
            print("  python start-python-windows.py --help # Show help")
            print("")
            print("System Features:")
            print("  - Auto-check and install dependencies")
            print("  - Auto-clean port conflicts")
            print("  - Start complete development environment")
            print("  - Windows-optimized configuration")
            return
    
    # Check and install dependencies
    if not check_windows_dependencies():
        print("\n❌ Dependency check failed, please resolve issues above")
        input("Press Enter to exit...")
        return
    
    # Clean existing processes
    kill_windows_process()
    
    # Start server
    if start_windows_server():
        print("👋 Thank you for using Neurotech Controls for AGI Motivational Framework!")
    else:
        print("❌ Startup failed")
        input("Press Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        input("Press Enter to exit...")