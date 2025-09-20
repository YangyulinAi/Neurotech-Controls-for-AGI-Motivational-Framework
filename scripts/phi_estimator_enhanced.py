#!/usr/bin/env python3
"""
Enhanced Φ (Phi) estimation with EMA smoothing for beautiful demo curves.
Integrated Information Theory calculation with exponential moving average.
"""
import numpy as np
from typing import Optional, Dict, Any
import time

class PhiEstimatorEnhanced:
    def __init__(self, method: str = "mock", max_channels: int = 8, alpha: float = 0.2):
        """
        Enhanced Phi estimator with EMA smoothing for demo-ready curves
        
        Args:
            method: Calculation method ('mock', 'IIT3.0', 'IIT4.0_light')
            max_channels: Maximum channels to process for performance
            alpha: EMA smoothing factor (0.0 = no smoothing, 1.0 = no memory)
        """
        self.method = method
        self.max_channels = max_channels
        self.alpha = alpha
        
        # EMA smoothing state
        self.phi_ema = None
        self.complexity_ema = None
        self.integration_ema = None
        
        # Performance tracking
        self.computation_times = []
        
    def smooth_value(self, new_value: float, current_ema: Optional[float]) -> float:
        """Apply exponential moving average smoothing"""
        if current_ema is None:
            return new_value
        return self.alpha * new_value + (1 - self.alpha) * current_ema
    
    def estimate_phi(self, data: np.ndarray, fs: int = 256) -> Dict[str, float]:
        """
        Enhanced Phi estimation with EMA smoothing
        
        Args:
            data: EEG data (channels, time_points)
            fs: Sampling frequency
            
        Returns:
            Dictionary with smoothed phi metrics
        """
        start_time = time.time()
        
        # Limit channels for performance
        if data.shape[0] > self.max_channels:
            # Select channels with highest variance for consciousness analysis
            channel_vars = np.var(data, axis=1)
            top_channels = np.argsort(channel_vars)[-self.max_channels:]
            data = data[top_channels, :]
        
        try:
            if self.method == "mock":
                # Enhanced mock with realistic patterns
                phi_raw = self._mock_phi_calculation(data, fs)
                complexity_raw = self._mock_complexity(data)
                integration_raw = self._mock_integration(data)
                
            elif self.method == "IIT3.0":
                # Simplified IIT 3.0 approximation
                phi_raw = self._iit3_approximation(data, fs)
                complexity_raw = self._compute_complexity(data)
                integration_raw = self._compute_integration(data)
                
            elif self.method == "IIT4.0_light":
                # Lightweight IIT 4.0 inspired calculation
                phi_raw = self._iit4_light_calculation(data, fs)
                complexity_raw = self._compute_complexity_v4(data)
                integration_raw = self._compute_integration_v4(data)
                
            else:
                # Fallback to mock
                phi_raw = self._mock_phi_calculation(data, fs)
                complexity_raw = self._mock_complexity(data)
                integration_raw = self._mock_integration(data)
            
            # Apply EMA smoothing for beautiful demo curves
            self.phi_ema = self.smooth_value(phi_raw, self.phi_ema)
            self.complexity_ema = self.smooth_value(complexity_raw, self.complexity_ema)
            self.integration_ema = self.smooth_value(integration_raw, self.integration_ema)
            
            # Track computation time
            computation_time = time.time() - start_time
            self.computation_times.append(computation_time)
            
            # Keep only recent computation times
            if len(self.computation_times) > 100:
                self.computation_times = self.computation_times[-50:]
            
            return {
                'phi': self.phi_ema,
                'complexity': self.complexity_ema,
                'integration': self.integration_ema,
                'computation_time_ms': computation_time * 1000,
                'avg_computation_time_ms': np.mean(self.computation_times) * 1000,
                'method': self.method,
                'channels_processed': data.shape[0],
                'smoothing_alpha': self.alpha
            }
            
        except Exception as e:
            print(f"Phi estimation error: {e}")
            # Return smoothed previous values on error
            return {
                'phi': self.phi_ema if self.phi_ema is not None else 0.0,
                'complexity': self.complexity_ema if self.complexity_ema is not None else 0.0,
                'integration': self.integration_ema if self.integration_ema is not None else 0.0,
                'computation_time_ms': 0.0,
                'error': str(e),
                'method': self.method
            }
    
    def _mock_phi_calculation(self, data: np.ndarray, fs: int) -> float:
        """Enhanced mock phi with realistic temporal dynamics"""
        # Simulate consciousness level based on signal complexity
        time_s = data.shape[1] / fs
        
        # Multi-frequency consciousness signature
        alpha_power = np.mean(np.abs(np.fft.fft(data, axis=1)[:, int(8*data.shape[1]/fs):int(13*data.shape[1]/fs)]))
        beta_power = np.mean(np.abs(np.fft.fft(data, axis=1)[:, int(13*data.shape[1]/fs):int(30*data.shape[1]/fs)]))
        gamma_power = np.mean(np.abs(np.fft.fft(data, axis=1)[:, int(30*data.shape[1]/fs):int(80*data.shape[1]/fs)]))
        
        # Consciousness-like dynamics
        base_phi = 0.3 + 0.4 * (gamma_power / (alpha_power + beta_power + 1e-6))
        
        # Add temporal variation for realistic demo
        temporal_modulation = 0.1 * np.sin(time_s * 0.5) + 0.05 * np.cos(time_s * 1.2)
        
        return np.clip(base_phi + temporal_modulation, 0.0, 1.0)
    
    def _mock_complexity(self, data: np.ndarray) -> float:
        """Mock complexity calculation"""
        return np.clip(np.std(data) * 2.0, 0.0, 1.0)
    
    def _mock_integration(self, data: np.ndarray) -> float:
        """Mock integration calculation"""
        cross_corr = np.corrcoef(data)
        return np.clip(np.mean(np.abs(cross_corr)), 0.0, 1.0)
    
    def _iit3_approximation(self, data: np.ndarray, fs: int) -> float:
        """Simplified IIT 3.0 approximation"""
        # Compute mutual information approximation
        mutual_info = self._compute_mutual_information(data)
        # Convert to phi-like measure
        return np.clip(mutual_info * 0.5, 0.0, 1.0)
    
    def _iit4_light_calculation(self, data: np.ndarray, fs: int) -> float:
        """Lightweight IIT 4.0 inspired calculation"""
        # Enhanced complexity measure
        integrated_info = self._compute_integrated_information_light(data)
        return np.clip(integrated_info, 0.0, 1.0)
    
    def _compute_mutual_information(self, data: np.ndarray) -> float:
        """Approximate mutual information between channels"""
        n_channels = data.shape[0]
        if n_channels < 2:
            return 0.0
        
        mi_sum = 0.0
        count = 0
        
        for i in range(min(n_channels, 8)):  # Limit for performance
            for j in range(i + 1, min(n_channels, 8)):
                # Simplified MI using correlation
                corr = np.corrcoef(data[i], data[j])[0, 1]
                mi_sum += -0.5 * np.log(1 - corr**2 + 1e-10)
                count += 1
        
        return mi_sum / max(count, 1)
    
    def _compute_integrated_information_light(self, data: np.ndarray) -> float:
        """Lightweight integrated information approximation"""
        # Multi-scale entropy as proxy for integrated information
        entropy_total = self._compute_sample_entropy(data.flatten())
        
        # Channel-wise entropy
        entropy_parts = np.mean([
            self._compute_sample_entropy(data[i]) 
            for i in range(min(data.shape[0], 8))
        ])
        
        # Integration as difference
        integration = entropy_total - entropy_parts
        return np.clip(integration, 0.0, 1.0)
    
    def _compute_sample_entropy(self, signal: np.ndarray, m: int = 2, r: float = 0.2) -> float:
        """Compute sample entropy as complexity measure"""
        try:
            N = len(signal)
            if N < m + 1:
                return 0.0
            
            # Simplified sample entropy calculation
            std_signal = np.std(signal)
            tolerance = r * std_signal
            
            def _maxdist(xi, xj, m):
                return max([abs(ua - va) for ua, va in zip(xi, xj)])
            
            patterns_m = np.array([signal[i:i + m] for i in range(N - m + 1)])
            patterns_m1 = np.array([signal[i:i + m + 1] for i in range(N - m)])
            
            A = sum(
                1 for i in range(len(patterns_m))
                for j in range(len(patterns_m))
                if i != j and _maxdist(patterns_m[i], patterns_m[j], m) <= tolerance
            )
            
            B = sum(
                1 for i in range(len(patterns_m1))
                for j in range(len(patterns_m1))
                if i != j and _maxdist(patterns_m1[i], patterns_m1[j], m + 1) <= tolerance
            )
            
            if A == 0 or B == 0:
                return 0.0
            
            return -np.log(B / A)
            
        except:
            return 0.0
    
    def _compute_complexity(self, data: np.ndarray) -> float:
        """IIT 3.0 style complexity"""
        return np.clip(np.std(data) * 1.5, 0.0, 1.0)
    
    def _compute_integration(self, data: np.ndarray) -> float:
        """IIT 3.0 style integration"""
        cross_corr = np.corrcoef(data)
        return np.clip(np.mean(np.abs(cross_corr)) * 0.8, 0.0, 1.0)
    
    def _compute_complexity_v4(self, data: np.ndarray) -> float:
        """IIT 4.0 style complexity"""
        return np.clip(self._compute_sample_entropy(data.flatten()) * 0.5, 0.0, 1.0)
    
    def _compute_integration_v4(self, data: np.ndarray) -> float:
        """IIT 4.0 style integration"""
        return np.clip(self._compute_integrated_information_light(data) * 0.7, 0.0, 1.0)
    
    def reset_smoothing(self):
        """Reset EMA smoothing state"""
        self.phi_ema = None
        self.complexity_ema = None
        self.integration_ema = None
        self.computation_times = []