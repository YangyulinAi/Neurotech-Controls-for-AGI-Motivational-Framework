#!/bin/bash

# EEG Emotion Prediction System - Setup Script
# This script automates the installation and setup process

set -e  # Exit on any error

echo "🧠 Neurotech Controls for AGI Motivational Framework - Setup"
echo "============================================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ from https://python.org/"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install -r python-requirements.txt
elif command -v pip &> /dev/null; then
    pip install -r python-requirements.txt
else
    echo "❌ pip is not available. Please install pip first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p data/training\ set
mkdir -p model
mkdir -p model_training

# Set permissions for executable files
chmod +x analyze_set_file.py
chmod +x start.sh

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "🚀 To start the system:"
echo "   ./start.sh"
echo ""
echo "🌐 Then open your browser to:"
echo "   http://localhost:5000"
echo ""
echo "📚 For detailed usage instructions, see README.md"