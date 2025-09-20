# Neural Axis BCI - Real-time EEG Emotion Recognition

> 📚 **Documentation Hub**: [INDEX.md](INDEX.md)

**Neural Axis** is a real-time Brain-Computer Interface platform for emotion recognition using EEG data and machine learning.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- EEG device (Muse2, OpenBCI, X.on, or standard 10-20 system)

### Installation
```bash
# Clone and install
git clone [your-repo-url]
cd neural-axis-bci
npm install
pip install -r requirements.txt

# Start the system
npm run dev
```

### Hardware Setup
See [Hardware Guide](HARDWARE_GUIDE.md) for device configuration.

### Interactive Tutorial
Open `notebooks/quick_start.ipynb` for a complete walkthrough.

## 🏗️ System Architecture

```
EEG Device → LSL Stream → Python Engine → WebSocket → React Dashboard
```

### Components
- **Frontend**: React + TypeScript with real-time visualization
- **Backend**: Node.js + Express with WebSocket streaming
- **Python Engine**: ONNX model inference and signal processing
- **Database**: PostgreSQL for data storage

## 🔧 Supported Devices

| Device | Channels | Sample Rate | Status |
|--------|----------|-------------|---------|
| Muse 2 | 4 | 256Hz | ✅ Supported |
| X.on | 8 | 500Hz | ✅ Supported |
| OpenBCI Cyton | 8 | 250Hz | ✅ Supported |
| Standard 10-20 | 16+ | Configurable | ✅ Supported |

## 📊 Key Features

- **Real-time Emotion Prediction**: Valence and arousal values
- **Multi-device Support**: Automatic device detection and configuration
- **Advanced Signal Processing**: Band power, differential entropy, FAA
- **ONNX Model Inference**: Cross-platform, high-performance
- **IIT Φ Integration**: Consciousness measurement (optional)
- **WebSocket Streaming**: Live data transmission

## 🛠️ Usage

### Training a Model
```bash
python scripts/train/train_labeled.py \
    --data_dir data/subjects \
    --device_name Muse2 \
    --epochs 50
```

### Real-time Analysis
```bash
# Start data acquisition
python scripts/lsl_receiver.py --device Muse2

# Launch web interface
npm run dev
# Access at http://localhost:5000
```

### Export to ONNX
```bash
python scripts/tools/export_onnx.py \
    --weights model/model_weight/ckpt.pt
```

## 📁 Project Structure

```
├── client/          # React frontend
├── server/          # Express backend
├── scripts/         # Python analysis engine
│   ├── train/       # Model training
│   ├── tools/       # ONNX export and benchmarking
│   └── tests/       # Test suites
├── configs/         # Device and feature configurations
├── notebooks/       # Interactive tutorials
└── model/           # Trained ONNX models
```

## 🔗 API Endpoints

### REST API
- `GET /api/data-files` - List EEG data files
- `POST /api/upload` - Upload recordings
- `POST /api/analyze` - Analyze EEG file

### WebSocket Events
- `emotion_prediction` - Real-time valence/arousal
- `phi_measurement` - IIT Φ values
- `system_status` - System health metrics

## 📚 Documentation

- **[Hardware Guide](HARDWARE_GUIDE.md)** - Device setup instructions
- **[X.on Setup](X_on_Setup_Guide.md)** - X.on specific configuration
- **[IIT Φ Integration](README_IIT_PHI.md)** - Consciousness measurement
- **[Quick Start Tutorial](quick_start.ipynb)** - Interactive walkthrough

## 🧪 Testing

```bash
# Python tests
python -m pytest scripts/tests/

# Frontend tests
npm test

# Hardware testing
python -c "from scripts.device_adapter import DeviceAdapter; print('Device adapter ready')"
```

## 🚀 Deployment

### Development
```bash
npm run dev
```

### Production
```bash
npm run build
npm run start
```

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

**Neural Axis BCI** - Real-time emotion recognition through EEG analysis.