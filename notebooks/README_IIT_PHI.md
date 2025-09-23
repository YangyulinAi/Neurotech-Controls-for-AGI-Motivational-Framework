# Integrated Information Theory (IIT) Φ Integration

> 🏠 **Back to Hub**: [INDEX.md](INDEX.md) | 📋 **Main README**: [README.md](README.md)

This document describes the integration of Integrated Information Theory (IIT) consciousness measurement capabilities into the Neural Axis BCI system.

## Overview

The IIT Φ (Phi) integration provides consciousness measurement capabilities by calculating the integrated information of EEG neural networks. This feature enables researchers to quantify consciousness levels during emotional state recognition.

## Core Components

### PhiEstimator Class (`src/phi_estimator.py`)

The main interface for IIT Φ calculations with multiple computation methods:

```python
from scripts.phi_estimator import PhiEstimator

# Initialize with mock method for demonstration
phi_estimator = PhiEstimator(method='mock', max_channels=8)

# Compute Φ for EEG data
import torch
eeg_data = torch.randn(4, 256)  # 4 channels, 256 samples
phi_value = phi_estimator.compute(eeg_data)
```

### Computation Methods

#### 1. Mock Method (`mock`)
- **Purpose**: Demonstration and testing
- **Output**: Realistic Φ values (0.01-0.15 range)
- **Performance**: Fastest, no external dependencies
- **Use Case**: Development and system validation

#### 2. IIT 3.0 Method (`IIT3.0`)
- **Purpose**: Research-grade consciousness measurement
- **Dependencies**: PyPhi library
- **Output**: Theoretically grounded Φ values
- **Performance**: Computationally intensive
- **Use Case**: Academic research and clinical applications

#### 3. IIT 4.0 Light Method (`IIT4.0_light`)
- **Purpose**: Optimized consciousness measurement
- **Dependencies**: PyPhi library
- **Output**: Efficient Φ approximation
- **Performance**: Balanced accuracy and speed
- **Use Case**: Real-time applications with consciousness monitoring

### Signal Binning Utilities (`src/utils/binning.py`)

Advanced preprocessing methods for IIT calculations:

#### Median Binning
```python
# Binary states based on median threshold
result = (eeg_data > median_value).int()
```

#### Threshold Binning
```python
# Binary states based on zero threshold
result = (eeg_data > 0).int()
```

#### Multi-level Binning
```python
# Ternary states: low (-1), medium (0), high (1)
# Converted to (0, 1, 2) for computation
```

## Configuration

### Installation

#### Core System (Mock Method Only)
```bash
pip install -r requirements.txt
```

#### Full IIT Capabilities
```bash
pip install -r requirements_phi.txt
```

### Configuration Parameters

#### Via Constructor
```python
phi_estimator = PhiEstimator(
    method='IIT3.0',           # Computation method
    max_channels=8,            # Maximum channels to process
    tau=1,                     # Time lag parameter
    bin_method='median'        # Binning strategy
)
```

#### Via YAML Configuration (`configs/phi.yaml`)
```yaml
phi:
  method: 'mock'
  max_channels: 8
  tau: 1
  bin_method: 'median'
  parallel_processing: true
```

## Training Integration

### Command Line Usage
```bash
# Basic training with Φ calculation
python scripts/train/train_labeled.py \
    --compute_phi \
    --phi_method mock \
    --data_dir data/subjects

# Advanced training with IIT 3.0
python scripts/train/train_labeled.py \
    --compute_phi \
    --phi_method IIT3.0 \
    --phi_max_channels 4 \
    --data_dir data/subjects
```

### Training Output
- **Model Metrics**: Standard emotion recognition performance
- **Φ Values**: Consciousness measurements per training sample
- **Visualization**: Φ progression plots in TensorBoard
- **Export**: Φ values saved with training metadata

## Real-time Integration

### WebSocket Broadcasting
The system broadcasts real-time Φ values alongside emotion predictions:

```javascript
// Frontend WebSocket event
{
  "type": "phi_measurement",
  "data": {
    "phi": 0.0234,
    "method": "mock",
    "channels": 4,
    "timestamp": "2025-01-03T07:15:26Z"
  }
}
```

### API Endpoint
```bash
# Test Φ calculation via REST API
curl -X POST http://localhost:5000/api/test-phi \
  -H "Content-Type: application/json" \
  -d '{"method": "mock", "channels": 4}'
```

## Research Applications

### Consciousness State Monitoring
- **Sleep Research**: Monitor consciousness transitions
- **Anesthesia**: Track awareness levels during procedures
- **Meditation Studies**: Quantify altered states of consciousness
- **Clinical Assessment**: Evaluate consciousness in brain injuries

### Emotion-Consciousness Correlation
- **Valence-Φ Relationships**: Study how positive/negative emotions relate to consciousness
- **Arousal-Φ Interactions**: Examine consciousness during high/low arousal states
- **Temporal Dynamics**: Track consciousness changes during emotional transitions

### Comparative Studies
- **Cross-Device Validation**: Compare Φ measurements across EEG systems
- **Method Comparison**: Evaluate different IIT computation approaches
- **Population Studies**: Analyze consciousness patterns across subjects

## Performance Considerations

### Computational Complexity
- **Mock Method**: O(1) - Constant time
- **IIT 3.0**: O(2^n) - Exponential in channel count
- **IIT 4.0 Light**: O(n^3) - Polynomial approximation

### Memory Requirements
- **Mock**: Minimal memory usage
- **IIT 3.0**: Exponential memory scaling
- **IIT 4.0 Light**: Linear memory scaling

### Optimization Strategies
```python
# Limit channels for real-time processing
phi_estimator = PhiEstimator(max_channels=4)

# Use parallel processing for batch analysis
phi_estimator = PhiEstimator(parallel=True)

# Cache results for repeated calculations
phi_estimator.enable_caching = True
```

## Validation and Testing

### Unit Tests
```bash
# Test all Φ computation methods
python -m pytest tests/test_phi_estimator.py

# Validate binning utilities
python -m pytest tests/test_binning.py
```

### Integration Tests
```bash
# Test with real EEG data
python tests/validate_phi_integration.py

# Performance benchmarking
python tests/benchmark_phi_methods.py
```

### Expected Outputs
- **Mock Method**: Values in 0.01-0.15 range
- **IIT Methods**: Theoretically valid Φ measurements
- **Performance**: Sub-second computation for ≤8 channels

## Troubleshooting

### Common Issues

#### PyPhi Installation Errors
```bash
# Install dependencies
pip install pyphi networkx numpy

# For compilation issues
export CC=gcc
pip install --no-cache-dir pyphi
```

#### Memory Errors with Large Channel Counts
```python
# Reduce channel count
phi_estimator = PhiEstimator(max_channels=4)

# Use light method
phi_estimator = PhiEstimator(method='IIT4.0_light')
```

#### Slow Computation
```python
# Enable parallel processing
phi_estimator = PhiEstimator(parallel=True)

# Use mock method for development
phi_estimator = PhiEstimator(method='mock')
```

## Future Enhancements

### Planned Features
- **Full IIT 4.0 Implementation**: Complete consciousness measurement
- **GPU Acceleration**: CUDA-optimized Φ computation
- **Temporal IIT**: Consciousness dynamics over time
- **Clinical Validation**: Medical-grade consciousness assessment

### Research Extensions
- **Multi-modal Integration**: Combine EEG Φ with other consciousness indicators
- **Machine Learning**: Predict consciousness states from EEG features
- **Network Analysis**: Graph-theoretic consciousness measures
- **Real-time Feedback**: Consciousness-based neurofeedback systems

## References

1. Tononi, G. (2008). Integrated Information Theory of Consciousness
2. Oizumi, M., et al. (2014). From the Phenomenology to the Mechanisms of Consciousness: IIT 3.0
3. Doerig, A., et al. (2021). The unfolding argument: Why IIT and other causal structure theories cannot explain consciousness
4. Mayner, W.G.P., et al. (2018). PyPhi: A toolbox for integrated information theory

## Support

### Documentation
- **PyPhi Documentation**: https://pyphi.readthedocs.io/
- **IIT Theory**: http://integratedinformationtheory.org/
- **Neural Axis BCI Guide**: [DOCUMENTATION.md](DOCUMENTATION.md)

### Community
- **IIT Research Community**: Academic collaborations and discussions
- **BCI Developers**: Technical implementation support
- **Consciousness Research**: Interdisciplinary research opportunities

---

The IIT Φ integration extends Neural Axis BCI beyond emotion recognition to include consciousness measurement, enabling comprehensive study of the relationship between emotional states and conscious awareness.
