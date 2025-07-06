#!/usr/bin/env python3
"""
Neurotech Controls for AGI Motivational Framework - Universal Python Startup Script
Cross-platform startup script supporting Windows, Ubuntu, and macOS
Developed by Neural Axis
"""

import subprocess
import sys
import os
import platform
import time
import signal
from pathlib import Path

def detect_platform():
    """Detect operating system platform"""
    system = platform.system().lower()
    if 'windows' in system:
        return 'windows'
    elif 'linux' in system:
        return 'linux'
    elif 'darwin' in system:
        return 'macos'
    else:
        return 'unknown'

def get_port_for_platform(platform_name):
    """Get port based on platform"""
    # Use 5000 for all platforms for simplicity
    return 5000

def check_dependencies():
    """Check dependencies"""
    print("🔍 Checking dependencies...")
    
    # Check Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js: {result.stdout.strip()}")
        else:
            print("❌ Node.js not installed")
            return False
    except FileNotFoundError:
        print("❌ Node.js not installed")
        return False
    
    # Check npm dependencies
    if not Path('node_modules').exists():
        print("❌ npm dependencies not installed, please run: npm install")
        return False
    else:
        print("✅ npm dependencies installed")
    
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
        print("Please run: pip install -r python-requirements.txt")
        return False
    else:
        print("✅ Python dependencies installed")
    
    return True

def kill_existing_process(port):
    """Kill existing processes on specified port"""
    platform_name = detect_platform()
    
    try:
        if platform_name == 'windows':
            # Windows: use netstat and taskkill
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            
            for line in lines:
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        print(f"🧹 Killing process on port {port} (PID: {pid})...")
                        subprocess.run(['taskkill', '/F', '/PID', pid], 
                                     capture_output=True)
        else:
            # Linux/macOS: use lsof and kill
            result = subprocess.run(['lsof', f'-ti:{port}'], 
                                  capture_output=True, text=True)
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        print(f"🧹 Killing process on port {port} (PID: {pid})...")
                        subprocess.run(['kill', '-9', pid], capture_output=True)
        
    except Exception as e:
        print(f"Error cleaning processes: {e}")

def start_server(port):
    """Start server"""
    platform_name = detect_platform()
    
    # Set environment variables
    env = os.environ.copy()
    env['PORT'] = str(port)
    env['NODE_ENV'] = 'development'
    
    platform_names = {
        'windows': 'Windows',
        'linux': 'Ubuntu/Linux',
        'macos': 'macOS'
    }
    
    print(f"🚀 Starting Neurotech Controls for AGI Motivational Framework on {platform_names.get(platform_name, platform_name)}...")
    print(f"   Port: {port} | Neural Axis")
    print(f"   Frontend URL: http://localhost:{port}")
    print("   Press Ctrl+C to stop service")
    print("")
    
    try:
        # Start npm development server
        if platform_name == 'windows':
            process = subprocess.Popen(['npm', 'run', 'dev'], env=env)
        else:
            process = subprocess.Popen(['npm', 'run', 'dev'], env=env)
        
        # Wait for process to end or be interrupted
        process.wait()
        
    except KeyboardInterrupt:
        print("\n⏹️  Received stop signal, shutting down server...")
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()
        print("✅ Server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False
    
    return True

def setup_dependencies():
    """Setup dependencies"""
    print("📦 Installing dependencies...")
    
    # Install npm dependencies
    print("Installing Node.js dependencies...")
    result = subprocess.run(['npm', 'install'], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ npm install failed: {result.stderr}")
        return False
    
    # Install Python dependencies
    print("Installing Python dependencies...")
    python_cmd = 'python' if platform.system() == 'Windows' else 'python3'
    result = subprocess.run([python_cmd, '-m', 'pip', 'install', '-r', 'python-requirements.txt'], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ pip install failed: {result.stderr}")
        return False
    
    print("✅ Dependencies installation completed")
    return True

def main():
    """Main function"""
    print("🧠 Neurotech Controls for AGI Motivational Framework - Python Launcher")
    print("=" * 70)
    
    # Detect platform and port
    platform_name = detect_platform()
    port = get_port_for_platform(platform_name)
    
    print(f"🖥️  Detected system: {platform_name}")
    print(f"🌐 Using port: {port}")
    print("")
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--setup':
            if setup_dependencies():
                print("Setup completed! Now you can run: python start_python.py")
            else:
                print("Setup failed, please check error messages")
            return
        elif sys.argv[1] == '--port':
            if len(sys.argv) > 2:
                try:
                    port = int(sys.argv[2])
                    print(f"Using custom port: {port}")
                except ValueError:
                    print("❌ Invalid port number")
                    return
        elif sys.argv[1] == '--help':
            print("Usage:")
            print("  python start_python.py           # Start system")
            print("  python start_python.py --setup   # Install dependencies")
            print("  python start_python.py --port <port>  # Use custom port")
            print("  python start_python.py --help    # Show help")
            return
    
    # Check dependencies
    if not check_dependencies():
        print("\n💡 Tip: Run 'python start_python.py --setup' to install dependencies")
        return
    
    # Clean existing processes
    kill_existing_process(port)
    
    # Start server
    start_server(port)

if __name__ == "__main__":
    main()