#!/usr/bin/env python3
"""
BCI Dashboard Controller
A desktop application to monitor and control the BCI dashboard system
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import time
import requests
import websocket
import json
import os
import sys
from pathlib import Path


class BCIController:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("BCI Dashboard Controller")
        self.root.geometry("500x600")
        self.root.resizable(True, True)

        # Get the absolute path of the script's directory
        # Handle both .py script and .exe compiled versions
        if getattr(sys, 'frozen', False):
            # Running as compiled exe
            # Get the real exe path using sys.argv[0]
            exe_path = os.path.abspath(sys.argv[0])
            exe_dir = os.path.dirname(exe_path)

            # If exe is in dist/ subdirectory, go up one level to pack/
            if os.path.basename(exe_dir) == 'dist':
                self.script_dir = os.path.dirname(exe_dir)  # Go up to pack/
            else:
                self.script_dir = exe_dir

            # Force change working directory to script location (pack/)
            # This ensures relative paths work correctly
            os.chdir(self.script_dir)

        else:
            # Running as .py script
            self.script_dir = os.path.dirname(os.path.abspath(__file__))

        # Since script is in online/pack/, go up one level to online/
        self.online_dir = os.path.dirname(self.script_dir)

        # Verify the directory structure exists
        if not os.path.exists(self.online_dir):
            # If online directory doesn't exist, assume we're in the wrong place
            # Look for online directory in current or parent directories
            current = os.getcwd()
            for _ in range(3):  # Search up to 3 levels up
                if os.path.exists(os.path.join(current, 'online')):
                    self.online_dir = os.path.join(current, 'online')
                    self.script_dir = os.path.join(self.online_dir, 'pack')
                    break
                elif os.path.basename(current) == 'online':
                    self.online_dir = current
                    self.script_dir = os.path.join(current, 'pack')
                    break
                current = os.path.dirname(current)

        # Status variables
        self.frontend_status = tk.StringVar(value="Offline")
        self.backend_status = tk.StringVar(value="Offline")
        self.data_status = tk.StringVar(value="No Data")

        # Process references
        self.frontend_process = None
        self.backend_process = None

        # Monitoring flags
        self.monitoring = False
        self.last_data_time = 0

        self.setup_ui()
        # Don't start monitoring automatically
        # self.start_monitoring()

    def setup_ui(self):
        """设置用户界面"""
        # 标题
        title_frame = ttk.Frame(self.root)
        title_frame.pack(pady=10)

        title_label = ttk.Label(title_frame, text="BCI Dashboard Controller",
                                font=("Arial", 16, "bold"))
        title_label.pack()

        # Status display area
        status_frame = ttk.LabelFrame(self.root, text="System Status", padding=10)
        status_frame.pack(pady=10, padx=20, fill="x")

        # Frontend status
        ttk.Label(status_frame, text="Frontend:").grid(row=0, column=0, sticky="w", pady=5)
        self.frontend_indicator = tk.Label(status_frame, text="●", font=("Arial", 12), fg="red")
        self.frontend_indicator.grid(row=0, column=1, sticky="w", padx=5)
        frontend_label = ttk.Label(status_frame, textvariable=self.frontend_status,
                                   font=("Arial", 10, "bold"))
        frontend_label.grid(row=0, column=2, sticky="w", padx=5)

        # Backend status
        ttk.Label(status_frame, text="Backend:").grid(row=1, column=0, sticky="w", pady=5)
        self.backend_indicator = tk.Label(status_frame, text="●", font=("Arial", 12), fg="red")
        self.backend_indicator.grid(row=1, column=1, sticky="w", padx=5)
        backend_label = ttk.Label(status_frame, textvariable=self.backend_status,
                                  font=("Arial", 10, "bold"))
        backend_label.grid(row=1, column=2, sticky="w", padx=5)

        # Data status
        ttk.Label(status_frame, text="Data Stream:").grid(row=2, column=0, sticky="w", pady=5)
        self.data_indicator = tk.Label(status_frame, text="●", font=("Arial", 12), fg="red")
        self.data_indicator.grid(row=2, column=1, sticky="w", padx=5)
        data_label = ttk.Label(status_frame, textvariable=self.data_status,
                               font=("Arial", 10, "bold"))
        data_label.grid(row=2, column=2, sticky="w", padx=5)

        # Control buttons area
        control_frame = ttk.LabelFrame(self.root, text="Control Panel", padding=10)
        control_frame.pack(pady=10, padx=20, fill="x")

        # Frontend control buttons
        frontend_frame = ttk.Frame(control_frame)
        frontend_frame.pack(fill="x", pady=5)

        ttk.Label(frontend_frame, text="Frontend:").pack(side="left")
        self.frontend_start_btn = ttk.Button(frontend_frame, text="Start",
                                             command=self.start_frontend)
        self.frontend_start_btn.pack(side="left", padx=5)

        self.frontend_stop_btn = ttk.Button(frontend_frame, text="Stop",
                                            command=self.stop_frontend, state="disabled")
        self.frontend_stop_btn.pack(side="left", padx=5)

        # Backend control buttons
        backend_frame = ttk.Frame(control_frame)
        backend_frame.pack(fill="x", pady=5)

        ttk.Label(backend_frame, text="Backend:").pack(side="left")
        self.backend_start_btn = ttk.Button(backend_frame, text="Start",
                                            command=self.start_backend)
        self.backend_start_btn.pack(side="left", padx=5)

        self.backend_stop_btn = ttk.Button(backend_frame, text="Stop",
                                           command=self.stop_backend, state="disabled")
        self.backend_stop_btn.pack(side="left", padx=5)

        # Quick control
        quick_frame = ttk.Frame(control_frame)
        quick_frame.pack(fill="x", pady=10)

        ttk.Button(quick_frame, text="Start All", command=self.start_all,
                   style="Accent.TButton").pack(side="left", padx=5)
        ttk.Button(quick_frame, text="Stop All", command=self.stop_all,
                   style="Accent.TButton").pack(side="left", padx=5)

        # Log display
        log_frame = ttk.LabelFrame(self.root, text="Status Log", padding=5)
        log_frame.pack(pady=5, padx=20, fill="both", expand=True)

        self.log_text = tk.Text(log_frame, height=6, wrap="word")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.log("BCI Controller started")
        self.log(f"Script directory: {self.script_dir}")
        self.log(f"Online directory: {self.online_dir}")

        # Debug information for exe detection
        if getattr(sys, 'frozen', False):
            self.log(f"Running as compiled exe")
            self.log(f"sys.argv[0]: {sys.argv[0]}")
            self.log(f"sys.executable: {sys.executable}")
            self.log(f"Current working dir: {os.getcwd()}")

            # Check if expected directories exist
            web_path = os.path.join(self.online_dir, 'web')
            src_path = os.path.join(self.online_dir, 'src')
            self.log(f"Web directory exists: {os.path.exists(web_path)} ({web_path})")
            self.log(f"Src directory exists: {os.path.exists(src_path)} ({src_path})")
        else:
            self.log(f"Running as Python script")

    def log(self, message):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")

    def check_frontend_status(self):
        """检查前端状态"""
        try:
            response = requests.get("http://localhost:5000", timeout=2)
            if response.status_code == 200:
                self.frontend_status.set("Online")
                self.frontend_indicator.config(fg="green")
                return True
        except:
            pass
        self.frontend_status.set("Offline")
        self.frontend_indicator.config(fg="red")
        return False

    def check_backend_status(self):
        """检查后端状态（检查你的BCI后端WebSocket服务器）"""
        try:
            # 根据你的runtime.yaml配置检查端口（默认尝试几个常用端口）
            ports_to_check = [8080, 8765, 9001, 8000]
            for port in ports_to_check:
                try:
                    ws = websocket.create_connection(f"ws://localhost:{port}/ws", timeout=1)
                    ws.close()
                    self.backend_status.set("Online")
                    self.backend_indicator.config(fg="green")
                    return True
                except:
                    continue
        except:
            pass
        self.backend_status.set("Offline")
        self.backend_indicator.config(fg="red")
        return False

    def check_data_flow(self):
        """检查数据流状态"""
        current_time = time.time()
        if current_time - self.last_data_time < 5:  # 5秒内有数据
            self.data_status.set("Active")
            self.data_indicator.config(fg="green")
        else:
            self.data_status.set("No Data")
            self.data_indicator.config(fg="red")

    def monitor_websocket(self):
        """监控WebSocket数据流"""
        # First check if backend is actually running before attempting connection
        if not self.check_backend_status():
            return

        def on_message(ws, message):
            self.last_data_time = time.time()

        def on_error(ws, error):
            # Only log non-connection errors
            error_str = str(error)
            if "10061" not in error_str:  # Don't log connection refused errors
                self.log(f"WebSocket monitoring error: {error}")

        def on_close(ws, close_status_code, close_msg):
            if self.monitoring and self.check_backend_status():
                # Only reconnect if backend is still running
                time.sleep(10)  # Longer delay
                if self.monitoring and self.check_backend_status():
                    threading.Thread(target=self.monitor_websocket, daemon=True).start()

        def on_open(ws):
            self.log("WebSocket monitoring connected")

        try:
            ws = websocket.WebSocketApp("ws://localhost:5000/ws",
                                        on_message=on_message,
                                        on_error=on_error,
                                        on_close=on_close,
                                        on_open=on_open)
            ws.run_forever()
        except Exception as e:
            # Don't retry automatically on connection failures
            pass

    def start_monitoring(self):
        """启动状态监控"""
        self.monitoring = True

        def monitor_loop():
            websocket_started = False
            while self.monitoring:
                self.check_frontend_status()
                backend_online = self.check_backend_status()

                # Only start WebSocket monitoring if backend is online and not already started
                if backend_online and not websocket_started:
                    self.log("Backend detected online, starting WebSocket monitoring...")
                    threading.Thread(target=self.monitor_websocket, daemon=True).start()
                    websocket_started = True
                elif not backend_online and websocket_started:
                    websocket_started = False

                self.check_data_flow()
                time.sleep(2)

        threading.Thread(target=monitor_loop, daemon=True).start()

    def stop_monitoring(self):
        """停止状态监控"""
        self.monitoring = False
        self.log("Monitoring stopped")

    def start_frontend(self):
        """启动前端"""
        try:
            # Frontend is in online/web (package.json is there)
            possible_frontend_paths = [
                os.path.join(self.online_dir, "web"),  # online/web
                os.path.join(self.script_dir, "..", "web"),  # ../web from pack
                "web",  # Relative path if run from online directory
                "."  # Fallback
            ]

            frontend_path = None
            for path in possible_frontend_paths:
                package_json_path = os.path.join(path, "package.json")
                if os.path.exists(package_json_path):
                    frontend_path = path
                    self.log(f"Found frontend at: {frontend_path}")
                    break

            if not frontend_path:
                error_msg = "Frontend not found\nSearched paths:\n"
                for path in possible_frontend_paths:
                    abs_path = os.path.abspath(path)
                    package_exists = "✓" if os.path.exists(os.path.join(abs_path, "package.json")) else "✗"
                    error_msg += f"{package_exists} {abs_path}\n"

                error_msg += f"\nScript dir: {self.script_dir}"
                error_msg += f"\nOnline dir: {self.online_dir}"
                error_msg += f"\nworking dir: {os.getcwd()}"

                # Show what's actually in the online directory
                if os.path.exists(self.online_dir):
                    contents = os.listdir(self.online_dir)
                    error_msg += f"\nOnline dir contents: {contents}"

                messagebox.showerror("Error", error_msg)
                self.log("Frontend startup failed - path not found")
                return

            # Try different npm command variations
            npm_commands = ["npm", "npm.cmd", "npx", "npx.cmd"]
            npm_found = False
            npm_cmd = None

            for cmd in npm_commands:
                try:
                    subprocess.run([cmd, "--version"], capture_output=True, check=True, cwd=frontend_path)
                    npm_cmd = cmd
                    npm_found = True
                    break
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue

            if not npm_found:
                # Try to find npm in common Windows locations
                common_npm_paths = [
                    "C:/Program Files/nodejs/npm.cmd",
                    "C:/Program Files (x86)/nodejs/npm.cmd",
                    os.path.expanduser("~/AppData/Roaming/npm/npm.cmd"),
                    os.path.expanduser("~/AppData/Local/npm/npm.cmd")
                ]

                for npm_path in common_npm_paths:
                    if os.path.exists(npm_path):
                        npm_cmd = npm_path
                        npm_found = True
                        break

            if not npm_found:
                messagebox.showerror("Error", f"npm not found in PATH or common locations\n"
                                              f"Tried: {', '.join(npm_commands)}\n"
                                              f"Working directory: {frontend_path}\n"
                                              "Please ensure Node.js is installed and npm is accessible")
                return

            self.log(f"Using npm command: {npm_cmd}")
            self.frontend_process = subprocess.Popen(
                [npm_cmd, "run", "dev"],
                cwd=frontend_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True  # Use shell for Windows compatibility
            )
            self.frontend_start_btn.config(state="disabled")
            self.frontend_stop_btn.config(state="normal")
            self.log("Starting frontend...")
            self.log("Frontend URL: http://localhost:5000")
            self.log("WebSocket: ws://localhost:5000/ws")

            # Wait a moment for service to start, then check status
            self.root.after(3000, self.check_frontend_status)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start frontend: {str(e)}\nError type: {type(e).__name__}")

    def stop_frontend(self):
        """停止前端"""
        if self.frontend_process:
            self.frontend_process.terminate()
            self.frontend_process = None
            self.frontend_start_btn.config(state="normal")
            self.frontend_stop_btn.config(state="disabled")
            self.log("Frontend stopped")

            # Immediately check status after stopping
            self.check_frontend_status()

    def start_backend(self):
        """启动后端"""
        try:
            # Check if required files exist before attempting to start
            main_py_path = os.path.join(self.online_dir, "src", "main.py")
            config_path = os.path.join(self.online_dir, "config", "runtime.yaml")

            # Verify essential files exist
            missing_files = []
            if not os.path.exists(main_py_path):
                missing_files.append("online/src/main.py")
            if not os.path.exists(config_path):
                missing_files.append("online/config/runtime.yaml")

            if missing_files:
                messagebox.showerror("Error",
                                     f"Required files missing:\n" + "\n".join(f"- {f}" for f in missing_files) +
                                     f"\n\nSearching from: {self.online_dir}")
                return

            # Check if required Python packages are available
            # Skip package check when running as exe to avoid recursive calls
            if not getattr(sys, 'frozen', False):
                required_packages = ['asyncio', 'yaml', 'numpy']
                missing_packages = []

                for package in required_packages:
                    try:
                        result = subprocess.run([sys.executable, "-c", f"import {package}"],
                                                capture_output=True, text=True)
                        if result.returncode != 0:
                            missing_packages.append(package)
                    except:
                        missing_packages.append(package)

                if missing_packages:
                    messagebox.showerror("Error",
                                         f"Required Python packages missing:\n" + "\n".join(
                                             f"- {p}" for p in missing_packages) +
                                         f"\n\nPlease install: pip install {' '.join(missing_packages)}")
                    return
            else:
                # When running as exe, assume packages are available or will be checked by the backend itself
                self.log("Running as exe - skipping package dependency check")

            # Get the real Python executable (not the exe wrapper)
            if getattr(sys, 'frozen', False):
                # When running as exe, find the system Python
                possible_python_paths = [
                    "python",  # Try system python first
                    "python.exe",
                    "py",
                    "py.exe",
                    r"C:\Python\python.exe",  # Common install paths
                    r"C:\Python39\python.exe",
                    r"C:\Python310\python.exe",
                    r"C:\Python311\python.exe",
                ]

                python_executable = None
                for py_path in possible_python_paths:
                    try:
                        result = subprocess.run([py_path, "--version"],
                                                capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            python_executable = py_path
                            self.log(f"Found Python: {py_path} ({result.stdout.strip()})")
                            break
                    except:
                        continue

                if not python_executable:
                    messagebox.showerror("Error",
                                         "Python not found in system PATH.\n"
                                         "Please ensure Python is installed and added to PATH.\n"
                                         "Searched: " + ", ".join(possible_python_paths))
                    return
            else:
                python_executable = sys.executable

            # Backend startup options in order of preference
            possible_backend_setups = [
                # (directory, command, description)
                (self.online_dir, [python_executable, "-m", "src.main"], "python -m src.main from online/"),
                (self.online_dir, [python_executable, "-u", "-m", "src.main"], "python -u -m src.main (unbuffered)"),
                (os.path.join(self.online_dir, "src"), [python_executable, "main.py"], "direct main.py from src/")
            ]

            backend_found = False
            for cwd_path, command, description in possible_backend_setups:
                # Check if the directory exists
                if not os.path.exists(cwd_path):
                    continue

                # For module commands, check if the module file exists
                if "-m" in command:
                    module_file = os.path.join(cwd_path, "src", "main.py")
                    if not os.path.exists(module_file):
                        continue
                # For direct script commands, check if the script exists
                else:
                    script_file = os.path.join(cwd_path, "main.py")
                    if not os.path.exists(script_file):
                        continue

                # Found a valid setup
                self.backend_process = subprocess.Popen(
                    command,
                    cwd=cwd_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                self.log(f"Found backend at: {cwd_path}")
                self.log(f"Starting backend: {description}")
                backend_found = True
                break

            if not backend_found:
                searched_info = "\n".join([f"- {desc} at {cwd}" for cwd, cmd, desc in possible_backend_setups])
                messagebox.showerror("Error",
                                     f"Backend script not found\nSearched locations:\n{searched_info}\n"
                                     f"Script directory: {self.script_dir}\n"
                                     f"Online directory: {self.online_dir}")
                return

            self.backend_start_btn.config(state="disabled")
            self.backend_stop_btn.config(state="normal")

            # Wait a moment for service to start, then check status
            self.root.after(2000, self.check_backend_status)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start backend: {str(e)}\nError type: {type(e).__name__}")

    def stop_backend(self):
        """停止后端"""
        if self.backend_process:
            self.backend_process.terminate()
            self.backend_process = None
            self.backend_start_btn.config(state="normal")
            self.backend_stop_btn.config(state="disabled")
            self.log("Backend stopped")

            # Immediately check status after stopping
            self.check_backend_status()

    def start_all(self):
        """启动全部服务"""
        self.start_frontend()
        time.sleep(1)
        self.start_backend()
        self.log("Starting all services...")

    def stop_all(self):
        """停止全部服务"""
        self.stop_frontend()
        self.stop_backend()
        self.log("All services stopped")

    def on_closing(self):
        """窗口关闭事件"""
        self.monitoring = False
        self.stop_all()
        self.root.destroy()

    def run(self):
        """运行应用程序"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()


if __name__ == "__main__":
    app = BCIController()
    app.run()