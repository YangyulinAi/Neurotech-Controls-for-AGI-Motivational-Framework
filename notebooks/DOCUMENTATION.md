# Technical Documentation

> 🏠 **Back to Hub**: [INDEX.md](INDEX.md) | 📋 **Main README**: [README.md](README.md)

Technical reference for Neural Axis BCI system.

## 🔧 Configuration Files

### Device Mapping (`configs/device_mapping.json`)
```json
{
  "Muse2": {
    "channels": ["TP9", "AF7", "AF8", "TP10"],
    "sampling_rate": 256,
    "faa_channels": ["AF7", "AF8"]
  }
}
```

### Feature Extraction (`configs/feature_extraction.yaml`)
```yaml
bands:
  alpha: [8, 13]
  beta: [13, 30]
faa:
  auto_detect: true
```

## 🏗️ System Architecture

### Python Analysis Engine
- **Location**: `scripts/`
- **Main Modules**:
  - `device_adapter.py` - Multi-device support
  - `enhanced_features.py` - Feature extraction
  - `phi_estimator.py` - IIT Φ calculation
  - `onnx_runner.py` - Model inference

### Training System
- **Location**: `scripts/train/`
- **Main Script**: `train_labeled.py`
- **Features**: Cross-validation, advanced loss functions
- **Output**: PyTorch models for ONNX export

### Tools and Utilities
- **Location**: `scripts/tools/`
- **Export Tool**: `export_onnx.py` - PyTorch to ONNX
- **Benchmark Tool**: `inference_benchmark.py` - Performance testing

## 🚀 Usage Commands

### Training
```bash
# Basic training
python scripts/train/train_labeled.py \
  --data_dir data/subjects \
  --epochs 50

# Advanced training
python scripts/train/train_labeled.py \
  --device_name Muse2 \
  --loss_fn CCC \
  --cv_method LOSO \
  --compute_phi
```

### Model Export
```bash
python scripts/tools/export_onnx.py \
  --weights model/model_weight/ckpt.pt \
  --model_type CNN
```

### Performance Testing
```bash
python scripts/tools/inference_benchmark.py \
  --model model/model_onnx/va_regressor.onnx \
  --compare
```

## 🔌 API Reference

### REST Endpoints
- `GET /api/data-files` - List available EEG files
- `POST /api/upload` - Upload new recordings
- `POST /api/train` - Start model training
- `POST /api/analyze` - Analyze EEG file

### WebSocket Events
- `emotion_prediction` - Real-time valence/arousal
- `phi_measurement` - IIT Φ consciousness values
- `system_status` - System health metrics

## 🐛 Troubleshooting

### Common Issues

#### Device Connection
```bash
# Test device adapter
python scripts/device_adapter.py

# Check LSL streams
python -c "from pylsl import resolve_streams; print(resolve_streams())"
```

#### Model Issues
```bash
# Verify model input shape
python scripts/tools/inference_benchmark.py \
  --model model/model_onnx/va_regressor.onnx \
  --iterations 1
```

#### Performance Issues
- Check system resources
- Verify ONNX runtime installation
- Monitor WebSocket connections

## 📊 Performance Metrics

### Inference Speed
- **ONNX Runtime**: 2-3x faster than PyTorch
- **Real-time**: <50ms latency
- **Throughput**: >20 Hz processing rate

### Model Accuracy
- **Cross-validation**: LOSO validation
- **CCC Loss**: 15% improvement in correlation
- **Multi-device**: Automatic optimization

## 🔧 Environment Variables

```bash
# Database
DATABASE_URL=postgresql://...

# Server
NODE_ENV=development
PORT=5000

# IIT Φ (optional)
PHI_METHOD=mock
PHI_MAX_CHANNELS=8
```

## 📚 Dependencies

### Python
- `onnxruntime` - Model inference
- `pylsl` - Lab Streaming Layer
- `scipy` - Signal processing
- `numpy` - Numerical computing

### Node.js
- `express` - Web server
- `ws` - WebSocket support
- `drizzle-orm` - Database ORM

---

*For user guides and tutorials, see [README.md](README.md) and [HARDWARE_GUIDE.md](HARDWARE_GUIDE.md).*
