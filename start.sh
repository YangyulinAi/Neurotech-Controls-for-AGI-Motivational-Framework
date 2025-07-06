#!/bin/bash

# EEG Emotion Prediction System - Start Script
# One-click startup for the complete system

set -e

echo "🧠 Starting Neurotech Controls for AGI Motivational Framework..."
echo "=================================================================="

# Check if Node.js dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "❌ Dependencies not found. Please run ./setup.sh first"
    exit 1
fi

# Check if model exists
if [ ! -f "model/va_regressor.onnx" ]; then
    echo "⚠️  No trained model found at model/va_regressor.onnx"
    echo "   You can upload a model through the web interface or train one"
fi

# Use port 5000 for all platforms for consistency
PORT=5000
echo "🚀 Using port 5000 for all platforms"

# Kill any existing processes on the port
echo "🧹 Cleaning up any existing processes on port $PORT..."
lsof -ti:$PORT | xargs kill -9 2>/dev/null || true

# Start the system
echo "🚀 Starting the system on port $PORT..."
echo "   Frontend: http://localhost:$PORT"
echo "   Press Ctrl+C to stop"
echo ""

# Start in development mode with port configuration
PORT=$PORT npm run dev