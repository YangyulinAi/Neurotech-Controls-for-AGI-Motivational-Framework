# Neurotech Controls for AGI Motivational Framework

> **🧠 Real-time Brain-Computer Interface for Emotion Recognition and AGI Motivation**

A comprehensive BCI system that processes EEG data in real-time to recognize emotional states and provide motivational feedback for AGI systems using advanced machine learning and consciousness measurement techniques.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/YangyulinAi/Neurotech-Controls-for-AGI-Motivational-Framework.git
cd Neurotech-Controls-for-AGI-Motivational-Framework

# Install dependencies
npm install
pip install -e .

# Start the system
npm run dev
```

## 📚 Documentation

> **📖 [Complete Documentation Hub](notebooks/INDEX.md)**

Our comprehensive documentation is organized in the `notebooks/` directory. The [INDEX.md](notebooks/INDEX.md) serves as the central hub for all guides, tutorials, and technical references.

### Key Documentation Links

- **[📋 Main Documentation](README.md)** - Project overview and installation
- **[🔧 Hardware Setup](notebooks/HARDWARE_GUIDE.md)** - EEG device configuration
- **[⚡ Quick Start Tutorial](notebooks/QUICK_START.ipynb)** - Interactive walkthrough
- **[📡 X.on Setup Guide](notebooks/X_ON_SETUP_GUIDE.md)** - X.on device specific setup
- **[🌀 IIT Φ Integration](notebooks/README_IIT_PHI.md)** - Consciousness measurement
- **[📑 Technical Reference](notebooks/DOCUMENTATION.md)** - Detailed technical docs

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Python        │
│   (React/TS)    │◄──►│   (Node.js)     │◄──►│   Analysis      │
│                 │    │                 │    │   Engine        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WebSocket     │    │   REST API      │    │   LSL Stream    │
│   Real-time     │    │   Endpoints     │    │   Processing    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AGI           │    │   Motivational  │    │   Consciousness │
│   Integration   │    │   Framework     │    │   Measurement   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Technology Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for build tooling
- **Tailwind CSS** for styling
- **Radix UI** for components
- **Framer Motion** for animations
- **Recharts** for data visualization

### Backend
- **Node.js** with Express
- **TypeScript** for type safety
- **WebSocket** for real-time communication
- **Drizzle ORM** for database management

### Python Analysis
- **Python 3.11+** with modern dependencies
- **ONNX Runtime** for model inference
- **NumPy & SciPy** for numerical computing
- **Matplotlib** for visualization
- **Lab Streaming Layer (LSL)** for EEG data

## 🧠 Supported EEG Devices

| Device | Channels | Sampling Rate | Status |
|--------|----------|---------------|--------|
| **Muse 2** | 4 | 256 Hz | ✅ Fully Supported |
| **X.on** | 8 | 500 Hz (→256 Hz) | ✅ Fully Supported |
| **OpenBCI Cyton** | 8-16 | 250-1000 Hz | ✅ Supported |
| **Standard 10-20** | 8-19+ | 256-1000 Hz | ✅ Supported |

## 🎯 Key Features

- **Real-time EEG Processing** - Live data acquisition and analysis
- **Emotion Recognition** - CNN-TCN hybrid model for valence/arousal prediction
- **AGI Motivational Framework** - Provides motivational feedback for AGI systems
- **Consciousness Measurement** - IIT Φ integration for consciousness assessment
- **Multi-device Support** - Compatible with major EEG hardware
- **Web-based Interface** - Modern React frontend with real-time visualization
- **Cross-platform** - Works on Windows, macOS, and Linux

## 🔬 Advanced Capabilities

- **Feature Extraction**: Spectrograms, differential entropy, Frontal Alpha Asymmetry (FAA)
- **Model Training**: Custom CNN-TCN architecture with CCC loss
- **Real-time Inference**: ONNX Runtime for cross-platform deployment
- **LSL Integration**: Lab Streaming Layer for seamless EEG data acquisition
- **WebSocket Communication**: Real-time data streaming to frontend
- **AGI Integration**: Motivational feedback system for artificial general intelligence

## 📊 Performance

- **Latency**: < 100ms end-to-end processing
- **Accuracy**: 85%+ emotion recognition accuracy
- **Throughput**: Real-time processing at 256 Hz
- **Scalability**: Supports multiple concurrent sessions

## 🛠️ Development

```bash
# Development setup
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server

# Python development
python scripts/main.py                    # Start Python backend
python scripts/train/train_labeled.py    # Train models
python scripts/tools/export_onnx.py      # Export ONNX models
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

## 🧪 Testing

```bash
# Python tests
python -m pytest scripts/tests/

# Frontend tests
npm test

# Hardware testing
python -c "from scripts.device_adapter import DeviceAdapter; print('Device adapter ready')"
```

## 📖 Learn More

For detailed information, tutorials, and technical documentation, visit our **[Documentation Hub](notebooks/INDEX.md)**.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](notebooks/INDEX.md#contributing-to-documentation) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Lab Streaming Layer (LSL) for real-time EEG data streaming
- PyTorch and ONNX Runtime for machine learning inference
- React and TypeScript for modern web development
- The BCI research community for inspiration and collaboration
- AGI research community for motivational framework concepts

---

**📖 [View Complete Documentation →](notebooks/INDEX.md)**
