# Hardware Integration Guide

This guide explains how to integrate different EEG devices with the Neural Axis BCI emotion recognition system.

## Supported Devices

The system currently supports the following EEG devices with built-in configurations:

### 1. Muse 2 Headband
- **Channels**: 4 (TP9, AF7, AF8, TP10)
- **Sampling Rate**: 256 Hz
- **FAA Channels**: AF7, AF8
- **Best For**: Consumer applications, meditation monitoring
- **Limitations**: Limited frontal coverage, no standard 10-20 positions

### 2. X.on EEG System
- **Channels**: 14 (FP1, FP2, F3, F4, F7, F8, C3, C4, P3, P4, O1, O2, T7, T8)
- **Sampling Rate**: 500 Hz
- **FAA Channels**: F3, F4
- **Best For**: Research applications, high-quality emotion recognition
- **Features**: Full 10-20 coverage, high sampling rate

### 3. OpenBCI Cyton Board
- **Channels**: 8 (Fp1, Fp2, C3, C4, P7, P8, O1, O2)
- **Sampling Rate**: 250 Hz
- **FAA Channels**: Fp1, Fp2
- **Best For**: DIY projects, research, customizable setups
- **Features**: Open-source, programmable

### 4. Standard 10-20 System
- **Channels**: 16+ (configurable)
- **Sampling Rate**: 256 Hz (default)
- **FAA Channels**: F3, F4
- **Best For**: Clinical and research applications
- **Features**: Industry standard positioning

## Quick Setup Guide

### Step 1: Device Configuration

1. **Identify your device** from the supported list above
2. **Configure the system** by specifying your device:

```bash
# During training
python train/train_labeled.py --device_name Muse2

# During real-time inference  
python src/main.py --device Muse2
```

### Step 2: Data Connection

#### Option A: Lab Streaming Layer (LSL) - Recommended
```bash
# Start LSL receiver
python src/lsl_receiver.py --device Muse2

# Start main application
python src/main.py --input_source lsl
```

#### Option B: Direct File Processing
```bash
# Process recorded files
python tests/analyze_set_file_onnx.py --file_path data/recording.set --device Muse2
```

### Step 3: Verification

Test your setup with a simple validation:

```bash
# Test device configuration
python -c "
from src.device_adapter import create_device_adapter
adapter = create_device_adapter('Muse2')
print('Device Info:', adapter.get_info())
"
```

## Adding New Device Support

To add support for a custom EEG device:

### 1. Create Device Configuration

Add your device to `config/device_mapping.json`:

```json
{
  "MyCustomDevice": {
    "channels": ["C3", "C4", "Cz", "Pz"],
    "sampling_rate": 512,
    "faa_channels": ["C3", "C4"],
    "description": "My custom 4-channel EEG device"
  }
}
```

### 2. Channel Mapping Guidelines

- **Use standard 10-20 names** when possible (Fp1, Fp2, F3, F4, etc.)
- **List channels in order** they appear in your data files
- **Specify FAA channels** that are most suitable for frontal alpha asymmetry
- **Set correct sampling rate** to enable automatic resampling

### 3. Test Your Configuration

```python
# Test your new device configuration
from src.device_adapter import create_device_adapter

adapter = create_device_adapter('MyCustomDevice')
info = adapter.get_info()
print("Device configuration:", info)

# Test FAA channel detection
faa_channels = adapter.find_faa_channels()
print("FAA channels:", faa_channels)
```

## Data Format Requirements

### File Formats
- **EEGLAB .set files**: Preferred format with full metadata
- **Raw arrays**: NumPy arrays with shape `(channels, samples)`
- **CSV files**: With channels as columns, samples as rows

### Data Structure
```python
# Expected data format for processing
data_shape = (n_channels, n_samples)
sampling_rate = 256  # Hz
channel_names = ["C3", "C4", "Cz", "Pz"]  # Match device config
```

### Quality Requirements
- **Sampling Rate**: Minimum 128 Hz, recommended 256+ Hz
- **Duration**: Minimum 2 seconds for emotion prediction
- **Channels**: At least 2 channels (preferably including frontal sites)
- **Data Quality**: Minimal artifacts, proper referencing

## Device-Specific Setup Instructions

### Muse 2 Setup

1. **Install Muse LSL**:
```bash
pip install muselsl
```

2. **Start streaming**:
```bash
muselsl stream --ppg --acc --gyro
```

3. **Connect to system**:
```bash
python src/lsl_receiver.py --device Muse2
```

### OpenBCI Setup

1. **Install OpenBCI GUI** or use Python SDK
2. **Configure channels** according to your montage
3. **Start LSL streaming** from GUI or:
```python
from openbci import OpenBCIBoard
board = OpenBCIBoard()
board.start_streaming()
```

### X.on Setup

1. **Use X.on software** to start LSL streaming
2. **Verify channel order** matches configuration
3. **Connect to system**:
```bash
python src/lsl_receiver.py --device X.on
```

## Troubleshooting

### Common Issues

#### 1. Channel Mismatch
**Problem**: Channels in data don't match device configuration
**Solution**: 
- Verify channel names in your data
- Update device configuration if needed
- Use channel mapping in adapter

#### 2. Sampling Rate Issues
**Problem**: Data has different sampling rate than expected
**Solution**:
- System automatically resamples data
- Check logs for resampling messages
- Update device config with correct rate

#### 3. FAA Calculation Errors
**Problem**: FAA channels not found or invalid
**Solution**:
- Check device has frontal channels
- Update FAA channels in configuration
- Use custom channel specification

#### 4. Data Quality Issues
**Problem**: Poor emotion recognition performance
**Solution**:
- Verify electrode impedances
- Check for artifacts (blinks, movements)
- Ensure proper referencing
- Use longer time windows

### Debugging Commands

```bash
# Test device adapter
python src/device_adapter.py

# Check LSL streams
python -c "from pylsl import resolve_streams; print(resolve_streams())"

# Verify model input shape
python tools/inference_benchmark.py --model model/va_regressor.onnx --iterations 1

# Test with sample data
python tests/test_preprocess.py
```

## Performance Optimization

### Real-time Processing
- **Use appropriate device**: Higher sampling rates need more processing power
- **Optimize window size**: Balance between latency and accuracy
- **Consider downsampling**: For devices with very high sampling rates
- **Enable GPU**: For ONNX inference when available

### Batch Processing
- **Use efficient file formats**: HDF5 or .mat for large datasets
- **Process in chunks**: For very long recordings
- **Parallel processing**: For multiple files

## Best Practices

### Data Collection
1. **Standardize setup**: Use consistent electrode positions
2. **Record metadata**: Include sampling rate, channel info, timestamps
3. **Quality control**: Monitor impedances during recording
4. **Calibration**: Record baseline and validation data

### System Integration
1. **Test thoroughly**: Validate with known data before deployment
2. **Monitor performance**: Check processing latency and accuracy
3. **Document setup**: Keep records of device configurations
4. **Version control**: Track configuration changes

### Troubleshooting Protocol
1. **Verify hardware**: Check device connectivity and status
2. **Check configuration**: Ensure device settings match system config
3. **Test data flow**: Confirm data reaches processing pipeline
4. **Validate output**: Check prediction quality and timing

## Support and Community

For additional help:
- **Documentation**: Check README.md and code comments
- **Issues**: Report problems on project repository
- **Community**: Join discussions about EEG device integration
- **Examples**: See `notebooks/quick_start.ipynb` for complete workflow

## Device Certification

When adding new devices, ensure they meet these criteria:

- ✅ **Minimum 2 channels** with at least one frontal site
- ✅ **Sampling rate ≥ 128 Hz** for adequate frequency resolution
- ✅ **LSL compatibility** or file export capability
- ✅ **Stable timing** for consistent sample intervals
- ✅ **Documentation** of channel positions and specifications

This comprehensive guide should help you integrate various EEG devices with the emotion recognition system. For specific device questions or new integrations, please refer to the device manufacturer's documentation and LSL streaming capabilities.