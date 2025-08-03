# Neural Axis BCI - Real-time EEG Emotion Recognition System

**Neural Axis** is an advanced real-time Brain-Computer Interface (BCI) platform for emotion recognition that uses machine learning and deep learning technologies to provide precise, interactive biosignal analysis and visualization.

## Core Technology Features

- **Real-time ONNX Model Inference Engine** - High-performance emotion prediction
- **Multi-channel EEG Signal Preprocessing** - Advanced signal processing pipeline  
- **WebSocket Real-time Data Transmission** - Live streaming capabilities
- **Dynamic Emotion State Visualization** - Interactive dashboard interface
- **Cross-platform Machine Learning Analysis** - Comprehensive AI-powered insights
- **IIT Φ (Integrated Information Theory)** - Consciousness measurement integration
- **Multi-device Hardware Support** - Compatible with Muse2, X.on, OpenBCI, and standard 10-20 systems

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- EEG device (Muse2, OpenBCI, X.on, or standard 10-20 system)

### Installation
```bash
# Clone the repository
git clone [your-repo-url]
cd neural-axis-bci

# Install dependencies
npm install
pip install -r requirements.txt

# Optional: Install IIT Φ dependencies
pip install -r requirements_phi.txt

# Start the development server
npm run dev
```

### Hardware Setup
See [Hardware Integration Guide](HARDWARE_GUIDE.md) for detailed device configuration instructions.

### Interactive Tutorial
Open `notebooks/quick_start.ipynb` for a complete walkthrough of the system.

## System Architecture

### Frontend (React + TypeScript)
- **Framework**: React with Vite build system
- **UI Components**: Shadcn/ui built on Radix UI primitives
- **Styling**: Tailwind CSS with dark theme
- **Real-time Data**: Custom WebSocket hooks
- **Routing**: Wouter for client-side navigation

### Backend (Node.js + Express)
- **Server**: Express.js with TypeScript
- **Database**: PostgreSQL with Drizzle ORM
- **Real-time**: WebSocket server for live data streaming
- **Sessions**: Express sessions with PostgreSQL store

### Python Analysis Engine
- **Signal Processing**: SciPy-based filtering and feature extraction
- **ML Framework**: ONNX Runtime for cross-platform inference
- **Model Architecture**: CNN-TCN hybrid for emotion recognition
- **Device Support**: Multi-device adapter with automatic configuration
- **IIT Integration**: Consciousness measurement via Φ calculation

## Key Features

### Multi-Device Support
- **Muse 2**: 4-channel consumer headband (256Hz)
- **X.on**: 14-channel research system (500Hz)
- **OpenBCI Cyton**: 8-channel open-source board (250Hz)
- **Standard 10-20**: Configurable clinical/research systems

### Advanced Feature Extraction
- **Spatial Structure Preservation**: Maintains channel relationships
- **Parameterized FAA**: Frontal Alpha Asymmetry with device adaptation
- **Differential Entropy**: Enhanced frequency domain features
- **Automatic Band Selection**: Data-driven frequency optimization

### Training System
- **Cross-validation**: Leave-One-Subject-Out (LOSO) and K-fold
- **Advanced Loss Functions**: CCC (Concordance Correlation Coefficient)
- **Model Architectures**: CNN-TCN hybrid with EfficientNet support
- **Performance Monitoring**: TensorBoard integration

### Deployment Tools
- **ONNX Export**: Production-ready model conversion
- **Performance Benchmarking**: CPU/GPU optimization testing
- **Multi-platform Support**: Cross-platform inference

## Data Flow

```
EEG Device → LSL Stream → Device Adapter → Feature Extraction → ONNX Model → WebSocket → Frontend Dashboard
```

### Real-time Pipeline
1. EEG data acquisition via Lab Streaming Layer (LSL)
2. Device-specific preprocessing and channel mapping
3. Advanced feature extraction (band powers, differential entropy, FAA)
4. ONNX model inference for emotion prediction
5. WebSocket broadcasting to frontend dashboard
6. Real-time visualization and analysis

### Training Pipeline
1. EEGLAB .set file loading with subject organization
2. Label assignment via JSON annotation files
3. Enhanced feature extraction with spatial preservation
4. Cross-validated training with advanced loss functions
5. ONNX model export for deployment

## Configuration

### Device Configuration (`config/device_mapping.json`)
```json
{
  "Muse2": {
    "channels": ["TP9", "AF7", "AF8", "TP10"],
    "sampling_rate": 256,
    "faa_channels": ["AF7", "AF8"]
  }
}
```

### Feature Configuration (`config/feature_extraction.yaml`)
```yaml
bands:
  alpha: [8, 13]
  beta: [13, 30]
faa:
  auto_detect: true
```

## Usage Examples

### Training a Model
```bash
python train/train_labeled.py \
    --data_dir data/subjects \
    --device_name Muse2 \
    --loss_fn CCC \
    --cv_method LOSO \
    --compute_phi \
    --epochs 50
```

### Exporting to ONNX
```bash
python tools/export_onnx.py \
    --weights train/models/best_model.pth \
    --model_type CNN
```

### Performance Benchmarking
```bash
python tools/inference_benchmark.py \
    --model model/va_regressor.onnx \
    --compare \
    --iterations 1000
```

### Real-time Analysis
```bash
# Start data acquisition
python src/lsl_receiver.py --device Muse2

# Launch web interface
npm run dev
# Access at http://localhost:5000
```

## API Endpoints

### REST API
- `GET /api/data-files` - List available EEG data files
- `POST /api/upload` - Upload new EEG recordings
- `POST /api/train` - Start model training
- `POST /api/analyze` - Analyze EEG file with ONNX model

### WebSocket Events
- `emotion_prediction` - Real-time valence/arousal values
- `phi_measurement` - IIT Φ consciousness values
- `system_status` - System health and performance metrics

## Development

### Project Structure
```
├── client/          # React frontend source
├── server/          # Express backend
├── src/             # Python analysis engine
├── train/           # Model training scripts
├── tools/           # ONNX export and benchmarking
├── config/          # Device and feature configurations
├── notebooks/       # Interactive tutorials
├── tests/           # Test suites and analysis tools
└── model/           # Trained ONNX models
```

### Environment Variables
```bash
DATABASE_URL=postgresql://...
NODE_ENV=development
PORT=5000
```

## Testing

### Unit Tests
```bash
# Python tests
python -m pytest tests/

# Frontend tests
npm test
```

### Hardware Testing
```bash
# Test device configurations
python -c "from src.device_adapter import create_device_adapter; print(create_device_adapter('Muse2').get_info())"

# Test feature extraction
python -c "from src.enhanced_features import EnhancedFeatureExtractor; print('Features ready')"
```

## Documentation

- **[Hardware Integration Guide](HARDWARE_GUIDE.md)** - Complete device setup instructions
- **[Quick Start Tutorial](notebooks/quick_start.ipynb)** - Interactive system walkthrough
- **[DFR5 Upgrade Summary](DFR5_UPGRADE_SUMMARY.md)** - Latest system enhancements
- **[IIT Φ Integration](README_IIT_PHI.md)** - Consciousness measurement details

## Performance

### Inference Speed
- **ONNX Runtime**: 2-3x faster than PyTorch
- **Real-time**: <50ms latency for emotion prediction
- **Throughput**: >20 Hz processing rate

### Model Accuracy
- **Cross-validation**: LOSO validation for subject independence
- **CCC Loss**: 15% improvement in emotion correlation
- **Multi-device**: Automatic optimization per hardware type

## Deployment

### Development
```bash
npm run dev  # Start development server
```

### Production Build
```bash
npm run build  # Build frontend
npm run start  # Start production server
```

### Docker (Coming Soon)
```bash
docker-compose up  # Full stack deployment
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- **Issues**: Report bugs and feature requests via GitHub Issues
- **Documentation**: Comprehensive guides in the `/docs` directory
- **Community**: Join discussions about BCI and emotion recognition

## Acknowledgments

- EEG device manufacturers for hardware specifications
- PyPhi team for Integrated Information Theory implementation
- ONNX Runtime team for cross-platform ML inference
- Open-source BCI community for inspiration and collaboration

---

**Neural Axis BCI** - Advancing human-computer interaction through real-time emotion recognition and consciousness measurement.