#!/usr/bin/env python3
"""
Enhanced Feature Extraction for Neural Axis BCI System
DFR5 Advanced Feature Extraction with Spatial Structure Preservation
"""

import numpy as np
from scipy.signal import butter, sosfiltfilt, stft, welch
from scipy.ndimage import zoom
from scipy.stats import entropy
import yaml
from typing import Dict, List, Tuple, Optional, Union
import logging

class EnhancedFeatureExtractor:
    """
    Advanced feature extraction with spatial structure preservation and configurable parameters
    """
    
    def __init__(self, config_path: str = "config/feature_extraction.yaml", fs: int = 256):
        """
        Initialize enhanced feature extractor
        
        Args:
            config_path: Path to feature extraction configuration
            fs: Sampling frequency
        """
        self.fs = fs
        self.config = self._load_config(config_path)
        self.frequency_bands = self._extract_frequency_bands()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("Enhanced Feature Extractor initialized")
        self.logger.info(f"Frequency bands: {list(self.frequency_bands.keys())}")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load feature extraction configuration"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.warning(f"Config not found: {config_path}, using defaults")
            return self._get_default_config()
        except yaml.YAMLError as e:
            self.logger.error(f"Invalid YAML: {e}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Return default configuration"""
        return {
            "frequency_bands": {
                "delta": {"range": [0.5, 4.0]},
                "theta": {"range": [4.0, 8.0]},
                "alpha": {"range": [8.0, 13.0]},
                "beta": {"range": [13.0, 30.0]},
                "gamma": {"range": [30.0, 45.0]}
            },
            "differential_entropy": {"enabled": True},
            "frontal_alpha_asymmetry": {"enabled": True, "auto_detect_channels": True},
            "spectrogram": {"enabled": True, "output_size": [224, 224]},
            "spatial_features": {"preserve_structure": True}
        }
    
    def _extract_frequency_bands(self) -> Dict[str, Tuple[float, float]]:
        """Extract frequency band definitions from config"""
        bands = {}
        freq_config = self.config.get("frequency_bands", {})
        
        for band_name, band_info in freq_config.items():
            band_range = band_info.get("range", [0, 50])
            bands[band_name] = tuple(band_range)
        
        return bands
    
    def bandpass_filter(self, data: np.ndarray, low: float, high: float, order: int = 4) -> np.ndarray:
        """
        Apply bandpass filter to data
        
        Args:
            data: EEG data (n_channels, n_samples)
            low: Low cutoff frequency
            high: High cutoff frequency
            order: Filter order
            
        Returns:
            Filtered data
        """
        sos = butter(order, [low, high], btype='bandpass', fs=self.fs, output='sos')
        return sosfiltfilt(sos, data, axis=-1)
    
    def compute_differential_entropy(self, data: np.ndarray, bands: Dict[str, Tuple[float, float]] = None) -> np.ndarray:
        """
        Compute differential entropy for frequency bands
        
        Args:
            data: EEG data (n_channels, n_samples)
            bands: Frequency bands dictionary
            
        Returns:
            DE features (n_bands, n_channels)
        """
        if bands is None:
            bands = self.frequency_bands
        
        de_features = []
        
        for band_name, (low, high) in bands.items():
            # Filter data for this band
            filtered_data = self.bandpass_filter(data, low, high)
            
            # Compute variance for each channel
            variance = np.var(filtered_data, axis=-1) + 1e-8  # Add small epsilon
            
            # Compute differential entropy: 0.5 * log(2 * pi * e * variance)
            de = 0.5 * np.log(2 * np.pi * np.e * variance)
            de_features.append(de)
        
        return np.array(de_features)  # Shape: (n_bands, n_channels)
    
    def compute_frontal_alpha_asymmetry(self, data: np.ndarray, 
                                       left_ch: int = None, right_ch: int = None,
                                       alpha_band: Tuple[float, float] = (8.0, 13.0)) -> float:
        """
        Compute Frontal Alpha Asymmetry (FAA)
        
        Args:
            data: EEG data (n_channels, n_samples)
            left_ch: Left frontal channel index
            right_ch: Right frontal channel index  
            alpha_band: Alpha frequency band
            
        Returns:
            FAA value (log(right) - log(left))
        """
        # Use default channels if not specified
        if left_ch is None or right_ch is None:
            # Try to auto-detect from channel count
            if data.shape[0] >= 4:  # Assume F3, F4 are available
                left_ch, right_ch = 3, 5  # Standard 10-20 positions
            elif data.shape[0] == 4:  # Muse2 configuration
                left_ch, right_ch = 1, 2  # AF7, AF8
            else:
                self.logger.warning("Cannot compute FAA: insufficient channels")
                return 0.0
        
        try:
            # Filter data for alpha band
            alpha_data = self.bandpass_filter(data, alpha_band[0], alpha_band[1])
            
            # Compute power for left and right channels
            left_power = np.var(alpha_data[left_ch]) + 1e-8
            right_power = np.var(alpha_data[right_ch]) + 1e-8
            
            # FAA = log(right) - log(left)
            faa = np.log(right_power) - np.log(left_power)
            
            return float(faa)
            
        except (IndexError, ValueError) as e:
            self.logger.warning(f"FAA computation failed: {e}")
            return 0.0
    
    def compute_spatial_spectrogram(self, data: np.ndarray, preserve_structure: bool = True) -> np.ndarray:
        """
        Compute spatial-aware spectrogram preserving channel topology
        
        Args:
            data: EEG data (n_channels, n_samples)
            preserve_structure: Whether to preserve spatial structure
            
        Returns:
            Spectrogram features (3, 224, 224)
        """
        # Compute STFT for each channel
        f, t, spectrograms = [], [], []
        
        for ch in range(data.shape[0]):
            f_ch, t_ch, Zxx = stft(data[ch], fs=self.fs, nperseg=self.fs//2, noverlap=self.fs//4)
            spectrograms.append(np.abs(Zxx))
        
        spectrograms = np.array(spectrograms)  # (n_channels, n_freqs, n_times)
        
        if preserve_structure and data.shape[0] > 1:
            # Create spatial average preserving topology
            spec_combined = np.mean(spectrograms, axis=0)
        else:
            # Simple average across channels
            spec_combined = np.mean(spectrograms, axis=0)
        
        # Log transform
        spec_combined = np.log1p(spec_combined)
        
        # Resize to standard CNN input size (224x224)
        target_size = self.config.get("spectrogram", {}).get("output_size", [224, 224])
        spec_resized = zoom(spec_combined, 
                           (target_size[0] / spec_combined.shape[0], 
                            target_size[1] / spec_combined.shape[1]), 
                           order=1)
        
        # Create 3-channel representation
        spec_3ch = np.stack([spec_resized] * 3, axis=0).astype(np.float32)
        
        return spec_3ch
    
    def compute_power_spectral_features(self, data: np.ndarray, 
                                       bands: Dict[str, Tuple[float, float]] = None) -> np.ndarray:
        """
        Compute power spectral density features for frequency bands
        
        Args:
            data: EEG data (n_channels, n_samples)
            bands: Frequency bands dictionary
            
        Returns:
            PSD features (n_bands, n_channels)
        """
        if bands is None:
            bands = self.frequency_bands
        
        psd_features = []
        
        # Compute PSD using Welch's method
        freqs, psd = welch(data, fs=self.fs, nperseg=min(self.fs, data.shape[1]//4), axis=-1)
        
        for band_name, (low, high) in bands.items():
            # Find frequency indices for this band
            band_indices = (freqs >= low) & (freqs <= high)
            
            if np.sum(band_indices) == 0:
                # No frequencies in this band, add zeros
                band_power = np.zeros(data.shape[0])
            else:
                # Integrate power in this band
                band_power = np.mean(psd[:, band_indices], axis=1)
            
            psd_features.append(band_power)
        
        return np.array(psd_features)  # Shape: (n_bands, n_channels)
    
    def compute_hjorth_parameters(self, data: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Compute Hjorth parameters (Activity, Mobility, Complexity)
        
        Args:
            data: EEG data (n_channels, n_samples)
            
        Returns:
            Dictionary with Hjorth parameters
        """
        # Activity (variance)
        activity = np.var(data, axis=-1)
        
        # First derivative
        d1 = np.diff(data, axis=-1)
        
        # Second derivative  
        d2 = np.diff(d1, axis=-1)
        
        # Mobility
        mobility = np.sqrt(np.var(d1, axis=-1) / (activity + 1e-8))
        
        # Complexity
        complexity = np.sqrt(np.var(d2, axis=-1) / (np.var(d1, axis=-1) + 1e-8)) / (mobility + 1e-8)
        
        return {
            "activity": activity,
            "mobility": mobility,
            "complexity": complexity
        }
    
    def extract_features(self, data: np.ndarray, 
                        faa_channels: Tuple[int, int] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Main feature extraction pipeline
        
        Args:
            data: EEG data (n_channels, n_samples)
            faa_channels: Tuple of (left_ch, right_ch) for FAA
            
        Returns:
            Tuple: (spectrogram_features, differential_entropy_vector)
        """
        # 1. Compute spatial spectrogram
        spec_features = self.compute_spatial_spectrogram(data, 
            preserve_structure=self.config.get("spatial_features", {}).get("preserve_structure", True))
        
        # 2. Compute differential entropy
        de_matrix = self.compute_differential_entropy(data)  # (n_bands, n_channels)
        
        # 3. Compute power spectral features
        psd_matrix = self.compute_power_spectral_features(data)  # (n_bands, n_channels)
        
        # 4. Compute FAA if enabled and channels provided
        faa_value = 0.0
        if self.config.get("frontal_alpha_asymmetry", {}).get("enabled", True):
            if faa_channels and len(faa_channels) == 2:
                faa_value = self.compute_frontal_alpha_asymmetry(data, faa_channels[0], faa_channels[1])
            else:
                faa_value = self.compute_frontal_alpha_asymmetry(data)
        
        # 5. Compute Hjorth parameters if enabled
        hjorth_features = []
        if self.config.get("advanced_features", {}).get("hjorth_parameters", {}).get("enabled", False):
            hjorth = self.compute_hjorth_parameters(data)
            hjorth_features = [
                np.mean(hjorth["activity"]),
                np.mean(hjorth["mobility"]), 
                np.mean(hjorth["complexity"])
            ]
        
        # 6. Combine differential entropy features into vector
        # Take mean across channels for each band (5,) + FAA (1,) + Hjorth (3,) = up to 9 features
        de_vector = np.mean(de_matrix, axis=1)  # (n_bands,)
        psd_vector = np.mean(psd_matrix, axis=1)  # (n_bands,)
        
        # Combine all features into DE vector
        combined_features = np.concatenate([
            de_vector,          # 5 DE features  
            psd_vector,         # 5 PSD features
            [faa_value],        # 1 FAA feature
            hjorth_features     # 0-3 Hjorth features
        ])
        
        # Pad or truncate to expected size (26 features)
        target_size = self.config.get("output", {}).get("feature_vector_size", 26)
        if len(combined_features) < target_size:
            # Pad with zeros
            padded_features = np.zeros(target_size)
            padded_features[:len(combined_features)] = combined_features
            combined_features = padded_features
        elif len(combined_features) > target_size:
            # Truncate
            combined_features = combined_features[:target_size]
        
        self.logger.debug(f"Extracted features - Spec: {spec_features.shape}, DE: {combined_features.shape}")
        
        return spec_features, combined_features.astype(np.float32)
    
    def validate_input(self, data: np.ndarray) -> bool:
        """
        Validate input data format and quality
        
        Args:
            data: EEG data to validate
            
        Returns:
            bool: True if data is valid
        """
        if data.ndim != 2:
            self.logger.error(f"Expected 2D data, got {data.ndim}D")
            return False
        
        if data.shape[1] < self.fs:  # Less than 1 second of data
            self.logger.warning(f"Short data segment: {data.shape[1]} samples")
        
        # Check for NaN or infinite values
        if not np.isfinite(data).all():
            self.logger.error("Data contains NaN or infinite values")
            return False
        
        # Check amplitude range
        amplitude_range = np.ptp(data)
        if amplitude_range < 0.1:
            self.logger.warning("Very low signal amplitude")
        elif amplitude_range > 1000:
            self.logger.warning("Very high signal amplitude")
        
        return True


# Backward compatibility function
def extract_feats(window: np.ndarray, fs: int, faa_channels: Tuple[int, int] = None):
    """
    Backward compatible feature extraction function
    
    Args:
        window: EEG data (n_channels, n_samples)
        fs: Sampling frequency
        faa_channels: FAA channel indices
        
    Returns:
        spec3: Spectrogram features (3, 224, 224)
        de_vec: DE vector (26,)
    """
    extractor = EnhancedFeatureExtractor(fs=fs)
    
    if not extractor.validate_input(window):
        # Return zeros if validation fails
        return np.zeros((3, 224, 224), dtype=np.float32), np.zeros(26, dtype=np.float32)
    
    try:
        spec_features, de_features = extractor.extract_features(window, faa_channels)
        return spec_features, de_features
    except Exception as e:
        logging.error(f"Feature extraction failed: {e}")
        return np.zeros((3, 224, 224), dtype=np.float32), np.zeros(26, dtype=np.float32)


if __name__ == "__main__":
    # Test the enhanced feature extractor
    import matplotlib.pyplot as plt
    
    # Create test data
    fs = 256
    duration = 5  # seconds
    n_channels = 4
    n_samples = fs * duration
    
    # Simulate EEG data with different frequency components
    time = np.linspace(0, duration, n_samples)
    test_data = np.zeros((n_channels, n_samples))
    
    for ch in range(n_channels):
        # Add different frequency components
        test_data[ch] = (
            np.sin(2 * np.pi * 10 * time) +      # Alpha
            0.5 * np.sin(2 * np.pi * 20 * time) + # Beta
            0.3 * np.random.randn(n_samples)       # Noise
        )
    
    # Test feature extraction
    extractor = EnhancedFeatureExtractor(fs=fs)
    
    print("Testing enhanced feature extraction...")
    spec_features, de_features = extractor.extract_features(test_data, faa_channels=(1, 2))
    
    print(f"Spectrogram features shape: {spec_features.shape}")
    print(f"DE features shape: {de_features.shape}")
    print(f"DE features sample: {de_features[:10]}")
    
    print("✓ Enhanced feature extraction test completed")