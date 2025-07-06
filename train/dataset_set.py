import numpy as np
import glob
import torch
from torch.utils.data import Dataset
import scipy.io
from scipy.signal import welch
import os

class EEGSetDataset(Dataset):
    """
    Dataset class for EEGLAB .set files with on-the-fly feature extraction
    """
    def __init__(self, set_dir, window_size=5, overlap=0.5, fs=256):
        """
        Args:
            set_dir: Directory containing .set files
            window_size: Window size in seconds for segmentation
            overlap: Overlap ratio between windows (0-1)
            fs: Sampling frequency
        """
        self.set_dir = set_dir
        self.window_size = window_size
        self.overlap = overlap
        self.fs = fs
        self.window_samples = int(window_size * fs)
        self.hop_samples = int(self.window_samples * (1 - overlap))
        
        # Find all .set files and create window indices
        self.items = []
        self._create_window_indices()
        
    def _create_window_indices(self):
        """Create indices for all windows across all files"""
        set_files = glob.glob(os.path.join(self.set_dir, '*.set'))
        
        for set_file in set_files:
            try:
                # Load MATLAB file
                mat_data = scipy.io.loadmat(set_file, struct_as_record=False, squeeze_me=True)
                
                # Extract EEG data - it's directly in the mat file, not nested in EEG
                if 'data' in mat_data:
                    data = mat_data['data']
                    if len(data.shape) == 2:  # channels x timepoints
                        n_channels, n_timepoints = data.shape
                        
                        # Create window indices
                        n_windows = (n_timepoints - self.window_samples) // self.hop_samples + 1
                        
                        for i in range(n_windows):
                            start_idx = i * self.hop_samples
                            end_idx = start_idx + self.window_samples
                            if end_idx <= n_timepoints:
                                self.items.append((set_file, start_idx, end_idx))
                                
            except Exception as e:
                print(f"Warning: Could not load {set_file}: {e}")
                continue
        
        print(f"Created {len(self.items)} windows from .set files")
    
    def __len__(self):
        return len(self.items)
    
    def __getitem__(self, idx):
        """Extract features for a single window"""
        set_file, start_idx, end_idx = self.items[idx]
        
        # Load and extract window
        mat_data = scipy.io.loadmat(set_file, struct_as_record=False, squeeze_me=True)
        data = mat_data['data'][:, start_idx:end_idx]  # channels x window_samples
        
        # Extract features
        spec_features = self._extract_spectrogram(data)
        de_features = self._extract_differential_entropy(data)
        
        # Generate synthetic labels for now (replace with real labels if available)
        valence = np.random.uniform(-1, 1)
        arousal = np.random.uniform(-1, 1)
        labels = np.array([valence, arousal], dtype=np.float32)
        
        return torch.from_numpy(spec_features), torch.from_numpy(de_features), torch.from_numpy(labels)
    
    def _extract_spectrogram(self, data):
        """Extract spectrogram features"""
        n_channels, n_samples = data.shape
        
        # Create 3-channel spectrogram (theta, alpha, beta)
        freq_bands = [
            (4, 8),   # theta
            (8, 13),  # alpha  
            (13, 30)  # beta
        ]
        
        spec_features = np.zeros((3, 64, 64))  # 3 bands x 64x64 image
        
        for band_idx, (low_freq, high_freq) in enumerate(freq_bands):
            band_power = np.zeros((8, 8))  # 8x8 spatial grid
            
            for ch in range(min(n_channels, 64)):
                # Calculate power spectral density
                freqs, psd = welch(data[ch], fs=self.fs, nperseg=min(256, n_samples//4))
                
                # Extract power in frequency band
                freq_mask = (freqs >= low_freq) & (freqs <= high_freq)
                if np.any(freq_mask):
                    power = np.mean(psd[freq_mask])
                    
                    # Map channel to spatial position (simplified)
                    row = ch // 8
                    col = ch % 8
                    if row < 8 and col < 8:
                        band_power[row, col] = power
            
            # Resize to 64x64
            from scipy.ndimage import zoom
            spec_features[band_idx] = zoom(band_power, (8, 8), order=1)
        
        return spec_features.astype(np.float32)
    
    def _extract_differential_entropy(self, data):
        """Extract differential entropy features"""
        n_channels = min(data.shape[0], 26)  # Limit to 26 channels
        de_features = np.zeros(26)
        
        for ch in range(n_channels):
            # Calculate differential entropy (simplified)
            signal = data[ch]
            # Remove DC component
            signal = signal - np.mean(signal)
            # Calculate variance as proxy for differential entropy
            variance = np.var(signal)
            de_features[ch] = np.log(2 * np.pi * np.e * variance + 1e-8)
        
        return de_features.astype(np.float32)