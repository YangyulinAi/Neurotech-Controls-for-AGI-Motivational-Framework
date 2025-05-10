# online/src/preprocess.py
import numpy as np
from scipy.signal import butter, sosfiltfilt, stft
from scipy.ndimage import zoom

def bandpass(data: np.ndarray, fs: int, low: float = 0.5, high: float = 45, order: int = 4) -> np.ndarray:
    """
    Apply a Chebyshev type II bandpass filter.

    Args:
        data: Array of shape (n_channels, n_times)
        fs: Sampling frequency
        low: Low cutoff frequency
        high: High cutoff frequency
        order: Filter order
    Returns:
        Filtered data of same shape
    """
    sos = butter(order, [low, high], btype='bandpass', fs=fs, output='sos')
    return sosfiltfilt(sos, data, axis=-1)

class Preprocessor:
    """
    Preprocessor for online data: bandpass filter and z-score normalization.
    """
    def __init__(self, fs: int, low: float, high: float):
        self.fs = fs
        self.sos = butter(4, [low, high], btype='bandpass', fs=fs, output='sos')

    def transform(self, data: np.ndarray) -> np.ndarray:
        """
        Filter and normalize data window.

        Args:
            data: Array of shape (n_samples, n_channels)
        Returns:
            Normalized array of same shape
        """
        filtered = sosfiltfilt(self.sos, data, axis=0)
        mean = np.mean(filtered, axis=0)
        std = np.std(filtered, axis=0) + 1e-6
        return (filtered - mean) / std


def extract_feats(window: np.ndarray, fs: int):
    """
    Extract spectrogram and differential entropy features from a data window.

    Args:
        window: Array of shape (n_channels, n_times)
        fs: Sampling frequency
    Returns:
        spec3: np.ndarray of shape (3, 224, 224)
        de_vec: np.ndarray of shape (26,)
    """
    # 1) Spectrogram branch
    _, _, Z = stft(window, fs, nperseg=fs//2, noverlap=fs//4)
    spec = np.log1p(np.abs(Z))          # (n_channels, F, T)
    spec = spec.mean(axis=0)            # collapse channels -> (F, T)
    # Resize to 224x224
    spec_resized = zoom(spec, (224 / spec.shape[0], 224 / spec.shape[1]), order=1)
    spec3 = np.stack([spec_resized] * 3, axis=0).astype('float32')  # (3, H, W)

    # 2) Differential Entropy branch
    bands = [(1,4), (4,8), (8,13), (13,30), (30,45)]
    de = []
    for low, high in bands:
        bp = bandpass(window, fs, low, high)
        var = np.var(bp, axis=-1) + 1e-6
        de.append(0.5 * np.log(2 * np.pi * np.e * var))
    de = np.array(de)                   # (5, n_channels)
    de_vec = de.mean(axis=1)            # (5,)

    # 3) Frontal Alpha Asymmetry (FAA)
    idx_af7, idx_af8 = 0, 1             # adjust to your montage
    left = np.var(bandpass(window[idx_af7], fs, 8, 13))
    right = np.var(bandpass(window[idx_af8], fs, 8, 13))
    faa = np.log(left+1e-6) - np.log(right+1e-6)
    de_vec = np.concatenate([de_vec, [faa]]).astype('float32')  # (6,)
    # Repeat/tile to length 26
    de_vec = np.tile(de_vec, 5)[:26]

    return spec3, de_vec
