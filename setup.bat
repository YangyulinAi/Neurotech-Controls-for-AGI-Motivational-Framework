@echo off
REM EEG Emotion Prediction System - Windows Setup Script

echo 🧠 EEG Emotion Prediction System - Setup (Windows)
echo ===============================================

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed. Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8+ from https://python.org/
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed

REM Install Node.js dependencies
echo 📦 Installing Node.js dependencies...
npm install

REM Install Python dependencies
echo 🐍 Installing Python dependencies...
pip install -r python-requirements.txt

REM Create necessary directories
echo 📁 Creating project directories...
if not exist "data\training set" mkdir "data\training set"
if not exist "model" mkdir "model"
if not exist "model_training" mkdir "model_training"

echo.
echo 🎉 Setup completed successfully!
echo.
echo 🚀 To start the system:
echo    start.bat
echo.
echo 🌐 Then open your browser to:
echo    http://localhost:5000
echo.
echo 📚 For detailed usage instructions, see README.md
pause