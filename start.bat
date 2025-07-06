@echo off
REM EEG Emotion Prediction System - Windows Start Script

echo 🧠 Starting EEG Emotion Prediction System...
echo =========================================

REM Check if Node.js dependencies are installed
if not exist "node_modules" (
    echo ❌ Dependencies not found. Please run setup.bat first
    pause
    exit /b 1
)

REM Check if model exists
if not exist "model\va_regressor.onnx" (
    echo ⚠️  No trained model found at model\va_regressor.onnx
    echo    You can upload a model through the web interface or train one
)

REM Kill any existing processes on port 5000 (Windows)
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5000" ^| find "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)

echo 🚀 Starting the system on port 5000...
echo    Frontend: http://localhost:5000
echo    Press Ctrl+C to stop
echo.

REM Set port for Windows
set PORT=5000

REM Start in development mode
npm run dev