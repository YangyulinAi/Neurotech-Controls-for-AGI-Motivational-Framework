# 🧠 Neurotech Controls for AGI Motivational Framework

A comprehensive machine learning-based EEG emotion prediction platform that provides real-time emotion analysis from EEG signals. The system uses a CNN-TCN neural network to predict valence and arousal values from EEG data in SET format.

*Developed by Neural Axis*

![System Dashboard](generated-icon.png)

## 🚀 Features

- **Real-time Emotion Analysis**: Live prediction of valence and arousal from EEG data
- **Machine Learning Pipeline**: CNN-TCN model trained on labeled EEG datasets
- **Interactive Dashboard**: Modern React-based web interface with real-time visualization
- **SET Format Support**: Compatible with EEGLAB SET files
- **Subject-based Organization**: Organized training data by subjects with emotion labels
- **Model Training**: Complete pipeline for training custom emotion prediction models

## 📋 Prerequisites

Before installing, ensure you have the following installed on your system:

- **Node.js** (v18 or higher) - [Download here](https://nodejs.org/)
- **Python** (3.8 or higher) - [Download here](https://python.org/)
- **Git** - [Download here](https://git-scm.com/)

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd eeg-emotion-prediction
```

### 2. Install Node.js Dependencies

```bash
npm install
```

### 3. Install Python Dependencies

```bash
pip install -r python-requirements.txt
```

Or if you prefer using conda:

```bash
conda create -n eeg-emotion python=3.11
conda activate eeg-emotion
pip install -r python-requirements.txt
```

### 4. Set Up Training Data (Optional)

If you have your own EEG data, organize it as follows:

```
data/training set/
├── s1/
│   ├── labels.json
│   └── *.set files
├── s2/
│   ├── labels.json
│   └── *.set files
└── ...
```

Each `labels.json` should contain emotion labels:

```json
{
  "filename1.set": {"valence": 0.5, "arousal": 0.7},
  "filename2.set": {"valence": -0.3, "arousal": 0.2}
}
```

## 🚀 Quick Start (One-Click Deployment)

### Option 1: Automated Setup (Recommended)

**Ubuntu/Linux (Port 5000):**
```bash
chmod +x setup.sh start-ubuntu.sh test-system.sh
./setup.sh          # Install all dependencies
./test-system.sh    # Verify installation (optional)
./start-ubuntu.sh   # Start system on port 5000
```

**Windows (Port 5000):**
```cmd
setup.bat           # Install all dependencies
start-windows.bat   # Start system on port 5000
```

**Windows Python Method:**
```cmd
python start-python-windows.py  # Python startup (auto-handles dependencies)
```

**Universal (Port 5000):**
```bash
chmod +x setup.sh start.sh
./setup.sh          # Install all dependencies
./start.sh          # Start system on port 5000 (all platforms)
```

### Option 2: Manual Setup

```bash
npm install
pip install -r python-requirements.txt
npm run dev  # Starts on port 5000 by default
```

### Option 3: Using Docker

```bash
docker-compose up -d
```

### Option 4: Production Deployment

```bash
npm run build
npm start
```

## 📖 Usage Guide

### 1. Access the Dashboard

Open your browser and navigate to:
```
http://localhost:5000
```

The system now uses port 5000 consistently across all platforms (Windows, Ubuntu, macOS) for simplicity and compatibility.

### 2. Upload Training Data

1. Click **"Upload Data Files"** on the home page
2. Select your SET files and upload them
3. The system will automatically organize them into subject folders
4. Default emotion labels will be created (you can modify them later)

### 3. Upload or Train a Model

**Option A: Upload Pre-trained Model**
1. Click **"Upload Model"**
2. Select your `.onnx` model file
3. The model will replace the current one

**Option B: Train a New Model**
1. Ensure you have training data with proper labels
2. Navigate to the training section
3. Configure training parameters:
   - Epochs: 30 (default)
   - Batch size: 16 (default)
   - Learning rate: 1e-4 (default)
   - Window size: 5.0 seconds
   - Overlap: 0.5 (50%)
4. Click **"Start Training"**
5. Monitor training progress in the logs

### 4. Analyze EEG Data

1. Click **"Select SET File"** 
2. Choose a SET file from your uploaded data
3. The system will:
   - Process the EEG data into 5-second windows
   - Extract spectrogram and differential entropy features
   - Run ML inference using the trained model
   - Display real-time predictions on the dashboard

### 5. Monitor Results

The dashboard displays:
- **Current Valence/Arousal**: Latest emotion predictions
- **Real-time Plots**: Time series and 2D emotion space visualization
- **Statistics**: Data point count, session time, and historical trends
- **Debug Console**: Connection status and system logs

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
NODE_ENV=development
PORT=5000
PYTHON_PATH=/usr/bin/python3
MODEL_PATH=./model/va_regressor.onnx
```

### Training Parameters

Modify training settings in the web interface or directly in scripts:

```python
# In train/train_labeled.py
parser.add_argument('--epochs', type=int, default=30)
parser.add_argument('--batch_size', type=int, default=16)
parser.add_argument('--lr', type=float, default=1e-4)
parser.add_argument('--window_size', type=float, default=5.0)
parser.add_argument('--overlap', type=float, default=0.5)
```

## 📁 Project Structure

```
├── client/                 # React frontend application
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── hooks/         # React hooks
│   │   ├── pages/         # Page components
│   │   └── types/         # TypeScript definitions
├── server/                 # Express backend server
│   ├── index.ts           # Server entry point
│   ├── routes.ts          # API routes
│   └── storage.ts         # Data storage
├── src/                   # Python ML inference modules
│   ├── onnx_runner.py     # ONNX model inference
│   ├── preprocess.py      # Signal preprocessing
│   └── utils/             # Utility functions
├── train/                 # Model training modules
│   ├── train_labeled.py   # Supervised training script
│   ├── model_cnn_tcn.py   # CNN-TCN model definition
│   └── dataset_set.py     # SET file dataset loader
├── data/                  # Training data (organized by subjects)
├── model/                 # Trained models
└── analyze_set_file.py    # Main analysis script
```

## 🔬 Technical Details

### Model Architecture

The system uses a hybrid CNN-TCN (Temporal Convolutional Network) architecture:

- **Spectrogram Branch**: CNN for processing frequency-domain features
- **Differential Entropy Branch**: Dense layers for statistical features
- **TCN Head**: Temporal convolution for sequence modeling
- **Output**: 2D emotion space (valence, arousal) in range [-1, 1]

### Data Processing Pipeline

1. **Signal Preprocessing**: Bandpass filtering (0.5-45 Hz), standardization
2. **Feature Extraction**: Spectrogram (3-channel) + Differential Entropy (26 features)
3. **Windowing**: 5-second windows with 50% overlap
4. **Model Inference**: ONNX runtime for cross-platform deployment

### Communication Architecture

- **Frontend ↔ Backend**: WebSocket for real-time data, REST API for controls
- **Backend ↔ Analysis**: HTTP POST for broadcasting ML predictions
- **Analysis Process**: Standalone Python process for ML inference

## 🐛 Troubleshooting

### Common Issues

**1. Port 5000 already in use**
```bash
# Kill process using port 5000
lsof -ti:5000 | xargs kill -9
# Or change port in package.json
```

**2. Python dependencies missing**
```bash
# Install specific packages
pip install torch onnx onnxruntime scipy numpy scikit-learn
```

**3. WebSocket connection failed**
- Check if the server is running on port 5000
- Verify firewall settings
- Try refreshing the browser

**4. Analysis not starting**
- Ensure SET files are properly formatted
- Check Python path in environment variables
- Verify model file exists at `model/va_regressor.onnx`

**5. Training fails**
- Ensure sufficient training data (multiple subjects)
- Check labels.json format in each subject folder
- Verify GPU/CPU resources are available

### Debug Mode

Enable detailed logging:

```bash
# Set debug environment
export DEBUG=true
npm run dev
```

Check browser console (F12) for frontend logs and terminal for backend logs.

## 🔄 Updates and Maintenance

### Updating the System

```bash
git pull origin main
npm install  # Update Node.js dependencies
pip install -r requirements.txt  # Update Python dependencies
```

### Backup Important Data

Regularly backup:
- Training data: `data/training set/`
- Trained models: `model/`
- Training checkpoints: `model_training/`

## 📚 API Reference

### REST Endpoints

- `GET /api/data-files` - List available SET files
- `POST /api/start-analysis` - Start EEG analysis
- `POST /api/start-training` - Start model training
- `POST /api/upload-model` - Upload ONNX model
- `POST /api/upload-data` - Upload SET files
- `POST /api/bci/broadcast` - Broadcast predictions (internal)

### WebSocket Events

- `connection` - Client connected
- `valence/arousal data` - Real-time predictions
- `analysis_complete` - Analysis finished


## 🤝 Contributing

Yangyulin Ai
Dr. Gabriel Axel Montes

## 📞 Support

For technical support or questions:
- Create an issue in the repository
- Check the troubleshooting section above
- Review system logs for error details

---

**Built with ❤️ using React, Node.js, Python, and PyTorch**
