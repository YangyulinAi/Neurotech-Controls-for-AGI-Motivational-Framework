@echo off
REM EEG Emotion Prediction System - Windows Start Script (Port 5000)
REM Windows专用启动脚本 - 端口5000

echo 🧠 启动脑电波情绪预测系统 (Windows端口5000)...
echo =================================================

REM Check if Node.js dependencies are installed
if not exist "node_modules" (
    echo ❌ 未找到依赖项，请先运行 setup.bat
    pause
    exit /b 1
)

REM Check if model exists
if not exist "model\va_regressor.onnx" (
    echo ⚠️  No trained model found at model\va_regressor.onnx
    echo    You can upload a model through the web interface or train a new one
)

REM Kill any existing processes on port 5000
echo 🧹 Cleaning existing processes on port 5000...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5000" ^| find "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)

echo 🚀 Starting Neurotech Controls for AGI Motivational Framework on Windows...
echo    Frontend URL: http://localhost:5000 ^| Neural Axis
echo    Press Ctrl+C to stop service
echo.

REM Set environment variables for Windows
set PORT=5000
set NODE_ENV=development

REM Start in development mode with port 5000
npm run dev