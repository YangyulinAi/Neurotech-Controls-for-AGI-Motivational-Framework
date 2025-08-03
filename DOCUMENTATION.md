# Neural Axis BCI - Complete Documentation Index

This document serves as the central hub for all Neural Axis BCI system documentation.

## Core Documentation

### 📋 [README.md](README.md)
**Main project overview and quick start guide**
- System architecture overview
- Installation instructions
- Basic usage examples
- API reference
- Performance metrics

### 🔧 [Hardware Integration Guide](HARDWARE_GUIDE.md)
**Complete guide for EEG device setup and integration**
- Supported devices (Muse2, X.on, OpenBCI, Standard 10-20)
- Device configuration procedures
- Channel mapping and FAA setup
- Troubleshooting common hardware issues
- Performance optimization tips

### 🚀 [DFR5 Upgrade Summary](DFR5_UPGRADE_SUMMARY.md)
**Comprehensive overview of the latest system enhancements**
- Multi-device support framework
- Enhanced feature extraction capabilities
- Advanced training system improvements
- ONNX export and deployment tools
- Performance benchmarking results

### 🧠 [IIT Φ Integration](README_IIT_PHI.md)
**Integrated Information Theory consciousness measurement**
- IIT Φ calculation methods (mock, IIT3.0, IIT4.0_light)
- Signal binning and preprocessing
- Configuration and optimization
- Research applications and interpretation

### 🎓 [Interactive Tutorial](notebooks/quick_start.ipynb)
**Complete hands-on walkthrough of the system**
- Step-by-step setup process
- Device configuration examples
- Feature extraction demonstrations
- Real-time emotion recognition simulation
- Model training and deployment workflow

## Technical Reference

### Configuration Files

#### Device Mapping (`config/device_mapping.json`)
Defines supported EEG devices and their specifications:
```json
{
  "DeviceName": {
    "channels": ["Ch1", "Ch2", ...],
    "sampling_rate": 256,
    "faa_channels": ["F3", "F4"],
    "description": "Device description"
  }
}
```

#### Feature Extraction (`config/feature_extraction.yaml`)
Controls advanced feature extraction parameters:
```yaml
bands:
  alpha: [8, 13]
  beta: [13, 30]
faa:
  auto_detect: true
  fallback_channels: ["F3", "F4"]
feature_extraction:
  preserve_spatial_structure: true
  use_differential_entropy: true
```

### Code Architecture

#### Frontend (React/TypeScript)
- **Location**: `client/`
- **Framework**: React + Vite + Tailwind CSS
- **Key Components**: Dashboard, VA Plane, Time Series Charts
- **Real-time**: WebSocket integration for live data

#### Backend (Node.js/Express)
- **Location**: `server/`
- **Framework**: Express.js with TypeScript
- **Database**: PostgreSQL with Drizzle ORM
- **API**: RESTful endpoints + WebSocket server

#### Python Analysis Engine
- **Location**: `src/`
- **Core Modules**:
  - `device_adapter.py` - Multi-device support
  - `enhanced_features.py` - Advanced feature extraction
  - `phi_estimator.py` - IIT Φ consciousness measurement
  - `preprocess.py` - Signal preprocessing pipeline
  - `onnx_runner.py` - Model inference engine

#### Training System
- **Location**: `train/`
- **Main Script**: `train_labeled.py`
- **Features**: Cross-validation, advanced loss functions, TensorBoard logging
- **Output**: PyTorch models ready for ONNX export

#### Tools and Utilities
- **Location**: `tools/`
- **Export Tool**: `export_onnx.py` - PyTorch to ONNX conversion
- **Benchmark Tool**: `inference_benchmark.py` - Performance testing
- **Analysis Tools**: Various scripts in `tests/`

## Usage Workflows

### 1. First-Time Setup
1. **System Requirements**: Python 3.8+, Node.js 16+, PostgreSQL
2. **Installation**: `npm install && pip install -r requirements.txt`
3. **Hardware Setup**: Follow [Hardware Guide](HARDWARE_GUIDE.md)
4. **Database Setup**: Configure PostgreSQL connection
5. **Verification**: Run system tests and tutorials

### 2. Data Collection and Training
1. **Data Preparation**: Organize EEG files in subject directories
2. **Label Creation**: Create `labels.json` files with emotion annotations
3. **Device Configuration**: Set up device adapter for your hardware
4. **Training**: Use enhanced training script with cross-validation
5. **Model Export**: Convert trained models to ONNX format

### 3. Real-time Deployment
1. **Model Loading**: Deploy ONNX models to inference engine
2. **Device Connection**: Start LSL streaming from EEG device
3. **Web Interface**: Launch React dashboard for visualization
4. **Monitoring**: Use performance benchmarking tools

### 4. System Customization
1. **Device Support**: Add new devices to device mapping configuration
2. **Feature Engineering**: Modify feature extraction parameters
3. **Model Architecture**: Customize CNN-TCN or implement EfficientNet
4. **UI Customization**: Modify React components for specific needs

## API Documentation

### REST Endpoints

#### Data Management
- `GET /api/data-files` - List available EEG recordings
- `POST /api/upload` - Upload new EEG data files
- `DELETE /api/data/:id` - Remove EEG data file
- `GET /api/subjects` - List available subjects/sessions

#### Model Operations
- `POST /api/train` - Start model training process
- `GET /api/models` - List available trained models
- `POST /api/analyze` - Analyze EEG file with specified model
- `GET /api/analysis/:id` - Retrieve analysis results

#### System Control
- `GET /api/status` - System health and performance metrics
- `POST /api/config` - Update system configuration
- `GET /api/devices` - List supported EEG devices
- `POST /api/test-phi` - Test IIT Φ calculation

### WebSocket Events

#### Incoming (Client → Server)
- `connect` - Establish WebSocket connection
- `start_analysis` - Begin real-time emotion analysis
- `stop_analysis` - Stop real-time processing
- `configure_device` - Set device parameters

#### Outgoing (Server → Client)
- `emotion_prediction` - Real-time valence/arousal values
- `phi_measurement` - IIT Φ consciousness measurements
- `system_status` - Performance and health metrics
- `analysis_complete` - Batch analysis finished
- `error` - Error messages and warnings

## Configuration Reference

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Server
NODE_ENV=development|production
PORT=5000
CORS_ORIGIN=http://localhost:3000

# Python
PYTHONPATH=./src
ONNX_MODEL_PATH=./model/va_regressor.onnx

# Optional: IIT Φ
PHI_METHOD=mock|IIT3.0|IIT4.0_light
PHI_MAX_CHANNELS=8
```

### Training Parameters
```bash
# Basic training
python train/train_labeled.py \
  --data_dir data/subjects \
  --epochs 50 \
  --batch_size 16 \
  --learning_rate 0.001

# Advanced training with DFR5 features
python train/train_labeled.py \
  --device_name Muse2 \
  --loss_fn CCC \
  --cv_method LOSO \
  --compute_phi \
  --use_batch_norm \
  --dropout_rate 0.2
```

## Troubleshooting

### Common Issues

#### Device Connection Problems
1. **Check LSL Stream**: Verify device is streaming via LSL
2. **Channel Mapping**: Ensure device configuration matches actual channels
3. **Sampling Rate**: Confirm sampling rate in configuration
4. **Driver Issues**: Update device drivers and software

#### Training Failures
1. **Data Format**: Verify EEGLAB .set files are properly formatted
2. **Labels**: Check labels.json files contain valid emotion annotations
3. **Memory**: Ensure sufficient RAM for training (8GB+ recommended)
4. **Dependencies**: Verify all Python packages are installed correctly

#### Performance Issues
1. **ONNX Runtime**: Install optimized ONNX Runtime for your platform
2. **GPU Support**: Configure CUDA for GPU acceleration if available
3. **Memory Management**: Monitor memory usage during real-time processing
4. **Network Latency**: Optimize WebSocket connection for real-time data

#### Frontend Issues
1. **CORS Errors**: Configure CORS_ORIGIN environment variable
2. **WebSocket Connection**: Check firewall and network settings
3. **Build Errors**: Clear node_modules and reinstall dependencies
4. **Browser Compatibility**: Use modern browsers with WebSocket support

### Getting Help

1. **Check Documentation**: Review relevant sections in this guide
2. **System Logs**: Examine console output for error messages
3. **Test Scripts**: Run diagnostic scripts in `tests/` directory
4. **Community Support**: Join discussions and report issues
5. **Hardware Vendors**: Contact EEG device manufacturers for device-specific issues

## Performance Optimization

### Real-time Processing
- **Buffer Size**: Optimize ring buffer size for your application
- **Window Overlap**: Balance accuracy vs. processing speed
- **Feature Selection**: Use only necessary features for real-time constraints
- **Model Complexity**: Choose appropriate model size for target hardware

### Batch Processing
- **Parallel Processing**: Use multiprocessing for large datasets
- **Memory Management**: Process data in chunks for large files
- **Storage Optimization**: Use efficient file formats (HDF5, compressed)
- **Caching**: Cache preprocessed features to avoid recomputation

### Deployment Optimization
- **ONNX Optimization**: Use ONNX Runtime optimization tools
- **Hardware Acceleration**: Leverage GPU/TPU when available
- **Load Balancing**: Distribute processing across multiple instances
- **Monitoring**: Implement comprehensive performance monitoring

## Future Development

### Planned Features
- **Additional Model Architectures**: EfficientNet implementation completion
- **Cloud Integration**: AWS/Azure deployment templates
- **Mobile Support**: React Native mobile dashboard
- **Advanced IIT**: Full IIT 4.0 implementation
- **Docker Deployment**: Containerized deployment solution

### Research Directions
- **Multimodal Integration**: Combine EEG with other biosignals
- **Personalized Models**: Subject-specific emotion recognition
- **Continuous Learning**: Online model adaptation
- **Explainable AI**: Model interpretability for clinical applications

---

This documentation is continuously updated as the system evolves. For the latest information, always refer to the most recent version of these documents.