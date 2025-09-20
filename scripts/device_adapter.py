#!/usr/bin/env python3
"""
Device Adapter for Neural Axis BCI System
Handles multi-device EEG data adaptation with automatic channel mapping and resampling
DFR5 Enhanced Multi-Device Support
"""

import json
import numpy as np
from scipy import signal
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Optional, Union
import yaml

class DeviceAdapter:
    """
    Adapts EEG data from various devices to a standard format
    Supports Muse2, X.on, OpenBCI Cyton, and Standard 10-20 systems
    """
    
    def __init__(self, device_config_path: str = "configs/device_mapping.json"):
        """
        Initialize device adapter with configuration
        
        Args:
            device_config_path: Path to device configuration file
        """
        self.device_config_path = device_config_path
        self.device_configs = self._load_device_configs()
        self.current_device = None
        self.target_fs = 256  # Standard sampling rate
        self.target_channels = 19  # Standard 10-20 channel count
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _load_device_configs(self) -> Dict:
        """Load device configuration from JSON file"""
        try:
            with open(self.device_config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Device config not found: {self.device_config_path}")
            return self._get_default_configs()
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in device config: {e}")
            return self._get_default_configs()
    
    def _get_default_configs(self) -> Dict:
        """Return default device configurations if config file is missing"""
        return {
            "devices": {
                "Standard_10_20": {
                    "channels": ["Fp1", "Fp2", "F7", "F3", "Fz", "F4", "F8",
                               "T7", "C3", "Cz", "C4", "T8",
                               "P7", "P3", "Pz", "P4", "P8", "O1", "O2"],
                    "sampling_rate": 256,
                    "faa_channels": {"left": "F3", "right": "F4"}
                }
            }
        }
    
    def set_device(self, device_name: str) -> bool:
        """
        Set the current device for adaptation
        
        Args:
            device_name: Name of the device (e.g., 'Muse2', 'X.on', 'OpenBCI_Cyton')
            
        Returns:
            bool: True if device is supported, False otherwise
        """
        if device_name in self.device_configs["devices"]:
            self.current_device = device_name
            self.logger.info(f"Device set to: {device_name}")
            return True
        else:
            self.logger.error(f"Unsupported device: {device_name}")
            available = list(self.device_configs["devices"].keys())
            self.logger.info(f"Available devices: {available}")
            return False
    
    def get_device_info(self, device_name: Optional[str] = None) -> Dict:
        """
        Get information about a device
        
        Args:
            device_name: Device name, or current device if None
            
        Returns:
            Dict: Device configuration information
        """
        device = device_name or self.current_device
        if device and device in self.device_configs["devices"]:
            return self.device_configs["devices"][device]
        return {}
    
    def resample_data(self, data: np.ndarray, original_fs: int, target_fs: int = None) -> np.ndarray:
        """
        Resample EEG data to target sampling rate
        
        Args:
            data: EEG data array (channels x samples)
            original_fs: Original sampling frequency
            target_fs: Target sampling frequency (default: self.target_fs)
            
        Returns:
            np.ndarray: Resampled data
        """
        if target_fs is None:
            target_fs = self.target_fs
            
        if original_fs == target_fs:
            return data
        
        # Calculate resampling ratio
        resample_ratio = target_fs / original_fs
        new_length = int(data.shape[1] * resample_ratio)
        
        # Resample each channel
        resampled_data = np.zeros((data.shape[0], new_length))
        for ch in range(data.shape[0]):
            resampled_data[ch] = signal.resample(data[ch], new_length)
        
        self.logger.info(f"Resampled from {original_fs}Hz to {target_fs}Hz")
        self.logger.info(f"Data shape: {data.shape} -> {resampled_data.shape}")
        
        return resampled_data
    
    def map_channels(self, data: np.ndarray, device_name: str = None) -> Tuple[np.ndarray, List[str]]:
        """
        Map device-specific channels to standard montage
        
        Args:
            data: EEG data array (channels x samples)
            device_name: Device name (uses current device if None)
            
        Returns:
            Tuple: (mapped_data, channel_names)
        """
        device = device_name or self.current_device
        if not device:
            self.logger.error("No device specified for channel mapping")
            return data, []
        
        device_config = self.get_device_info(device)
        if not device_config:
            self.logger.error(f"No configuration found for device: {device}")
            return data, []
        
        device_channels = device_config.get("channels", [])
        n_device_channels = len(device_channels)
        
        # Handle different channel counts
        if data.shape[0] != n_device_channels:
            self.logger.warning(f"Data has {data.shape[0]} channels, expected {n_device_channels}")
            # Take minimum available channels
            n_channels = min(data.shape[0], n_device_channels)
            data = data[:n_channels]
            device_channels = device_channels[:n_channels]
        
        # For now, return the data with device channel names
        # In a full implementation, this would map to standard 10-20 positions
        self.logger.info(f"Mapped {len(device_channels)} channels for {device}")
        
        return data, device_channels
    
    def get_faa_channel_indices(self, device_name: str = None) -> Tuple[Optional[int], Optional[int]]:
        """
        Get the indices for Frontal Alpha Asymmetry channels
        
        Args:
            device_name: Device name (uses current device if None)
            
        Returns:
            Tuple: (left_channel_index, right_channel_index) or (None, None) if not found
        """
        device = device_name or self.current_device
        if not device:
            return None, None
        
        device_config = self.get_device_info(device)
        faa_config = device_config.get("faa_channels", {})
        
        if not faa_config:
            return None, None
        
        left_ch = faa_config.get("left")
        right_ch = faa_config.get("right")
        channels = device_config.get("channels", [])
        
        try:
            left_idx = channels.index(left_ch) if left_ch in channels else None
            right_idx = channels.index(right_ch) if right_ch in channels else None
            return left_idx, right_idx
        except (ValueError, AttributeError):
            return None, None
    
    def adapt_data(self, data: np.ndarray, device_name: str, original_fs: int = None) -> Dict:
        """
        Complete adaptation pipeline for device data
        
        Args:
            data: Raw EEG data (channels x samples)
            device_name: Name of the source device
            original_fs: Original sampling frequency (uses device config if None)
            
        Returns:
            Dict: Adapted data with metadata
        """
        if not self.set_device(device_name):
            raise ValueError(f"Unsupported device: {device_name}")
        
        device_config = self.get_device_info(device_name)
        
        # Get original sampling rate from config if not provided
        if original_fs is None:
            original_fs = device_config.get("sampling_rate", 256)
        
        # Step 1: Channel mapping
        mapped_data, channel_names = self.map_channels(data, device_name)
        
        # Step 2: Resampling
        if original_fs != self.target_fs:
            resampled_data = self.resample_data(mapped_data, original_fs, self.target_fs)
        else:
            resampled_data = mapped_data
        
        # Step 3: Get FAA channel indices
        faa_left, faa_right = self.get_faa_channel_indices(device_name)
        
        # Return adaptation results
        adaptation_result = {
            "data": resampled_data,
            "channels": channel_names,
            "sampling_rate": self.target_fs,
            "original_fs": original_fs,
            "device": device_name,
            "faa_channels": {
                "left_idx": faa_left,
                "right_idx": faa_right,
                "left_name": device_config.get("faa_channels", {}).get("left"),
                "right_name": device_config.get("faa_channels", {}).get("right")
            },
            "adaptation_applied": {
                "channel_mapping": True,
                "resampling": original_fs != self.target_fs,
                "faa_detection": faa_left is not None and faa_right is not None
            }
        }
        
        self.logger.info(f"Adaptation complete for {device_name}")
        self.logger.info(f"Output shape: {resampled_data.shape}")
        self.logger.info(f"FAA channels: {faa_left}, {faa_right}")
        
        return adaptation_result
    
    def validate_data(self, data: np.ndarray, device_name: str = None) -> Dict:
        """
        Validate EEG data quality and characteristics
        
        Args:
            data: EEG data array
            device_name: Device name for validation rules
            
        Returns:
            Dict: Validation results
        """
        validation_results = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "statistics": {}
        }
        
        # Basic shape validation
        if data.ndim != 2:
            validation_results["errors"].append(f"Expected 2D data, got {data.ndim}D")
            validation_results["valid"] = False
        
        # Amplitude validation
        amplitude_range = np.ptp(data, axis=1)  # Peak-to-peak per channel
        mean_amplitude = np.mean(amplitude_range)
        
        if mean_amplitude < 1.0:
            validation_results["warnings"].append("Low signal amplitude detected")
        elif mean_amplitude > 200.0:
            validation_results["warnings"].append("High signal amplitude detected")
        
        # Store statistics
        validation_results["statistics"] = {
            "mean_amplitude": float(mean_amplitude),
            "max_amplitude": float(np.max(data)),
            "min_amplitude": float(np.min(data)),
            "std_amplitude": float(np.std(data)),
            "shape": data.shape
        }
        
        return validation_results


def load_feature_config(config_path: str = "configs/feature_extraction.yaml") -> Dict:
    """
    Load feature extraction configuration
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Dict: Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.warning(f"Feature config not found: {config_path}")
        return {}
    except yaml.YAMLError as e:
        logging.error(f"Invalid YAML in feature config: {e}")
        return {}


# Example usage and testing
if __name__ == "__main__":
    # Initialize adapter
    adapter = DeviceAdapter()
    
    # Test with simulated Muse2 data
    print("Testing Muse2 adaptation...")
    muse_data = np.random.randn(4, 1280)  # 4 channels, 5 seconds at 256Hz
    
    try:
        result = adapter.adapt_data(muse_data, "Muse2", original_fs=256)
        print(f"Adaptation successful: {result['data'].shape}")
        print(f"FAA channels: {result['faa_channels']}")
    except Exception as e:
        print(f"Adaptation failed: {e}")
    
    # Test validation
    validation = adapter.validate_data(muse_data)
    print(f"Validation: {'PASS' if validation['valid'] else 'FAIL'}")
    if validation["warnings"]:
        print(f"Warnings: {validation['warnings']}")