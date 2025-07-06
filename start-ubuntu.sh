#!/bin/bash

# Neurotech Controls for AGI Motivational Framework - Ubuntu Start Script (Port 5000)
# Ubuntu startup script using port 5000 for consistency

set -e

echo "🧠 Starting Neurotech Controls for AGI Motivational Framework (Ubuntu Port 5000)..."
echo "================================================================================="

# Check if Node.js dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "❌ Dependencies not found, please run ./setup.sh first"
    exit 1
fi

# Check if model exists
if [ ! -f "model/va_regressor.onnx" ]; then
    echo "⚠️  No trained model found at model/va_regressor.onnx"
    echo "   You can upload a model through the web interface or train a new one"
fi

# Kill any existing processes on port 5000
echo "🧹 Cleaning existing processes on port 5000..."
lsof -ti:5000 | xargs kill -9 2>/dev/null || true

# Start the system on port 5000
echo "🚀 Starting system on port 5000..."
echo "   Frontend URL: http://localhost:5000"
echo "   Press Ctrl+C to stop service"
echo ""

# Set environment variables for Ubuntu
export PORT=5000
export NODE_ENV=development

# Start in development mode with port 5000
npm run dev