"""
EEG 信号二值化和多阶符号化工具
用于将连续的 EEG 信号转换为离散状态，以支持 IIT Φ 计算
"""

import torch
import numpy as np
from typing import Literal, Tuple


def median_binarize(signal: torch.Tensor, dim: int = -1) -> torch.Tensor:
    """基于中位数的二值化
    
    Args:
        signal: 输入信号张量
        dim: 计算中位数的维度
    
    Returns:
        二值化后的信号 (0 或 1)
    """
    median = signal.median(dim=dim, keepdim=True).values
    return (signal > median).int()


def threshold_binarize(signal: torch.Tensor, threshold: float = 0.0) -> torch.Tensor:
    """基于固定阈值的二值化
    
    Args:
        signal: 输入信号张量
        threshold: 二值化阈值
    
    Returns:
        二值化后的信号 (0 或 1)
    """
    return (signal > threshold).int()


def zscore_binarize(signal: torch.Tensor, dim: int = -1) -> torch.Tensor:
    """基于 Z-score 的二值化
    
    Args:
        signal: 输入信号张量
        dim: 计算均值和标准差的维度
    
    Returns:
        二值化后的信号 (0 或 1)
    """
    mean = signal.mean(dim=dim, keepdim=True)
    return (signal > mean).int()


def multi_level_discretize(
    signal: torch.Tensor, 
    n_levels: int = 3, 
    method: Literal["uniform", "quantile", "zscore"] = "zscore",
    dim: int = -1
) -> torch.Tensor:
    """多阶离散化
    
    Args:
        signal: 输入信号张量
        n_levels: 离散化级别数
        method: 离散化方法
        dim: 计算统计量的维度
    
    Returns:
        离散化后的信号 (0 到 n_levels-1)
    """
    if method == "uniform":
        # 基于信号范围的均匀分割
        min_val = signal.min(dim=dim, keepdim=True).values
        max_val = signal.max(dim=dim, keepdim=True).values
        range_val = max_val - min_val
        
        # 避免除零
        range_val = torch.where(range_val == 0, torch.ones_like(range_val), range_val)
        
        normalized = (signal - min_val) / range_val
        discretized = (normalized * n_levels).clamp(0, n_levels - 1).int()
        
    elif method == "quantile":
        # 基于分位数的分割
        # 简化实现：使用 numpy 进行分位数计算
        signal_np = signal.numpy()
        result = np.zeros_like(signal_np, dtype=int)
        
        for i in range(signal_np.shape[0] if len(signal_np.shape) > 1 else 1):
            if len(signal_np.shape) > 1:
                channel_data = signal_np[i]
            else:
                channel_data = signal_np
                
            quantiles = np.linspace(0, 1, n_levels + 1)
            thresholds = np.quantile(channel_data, quantiles)
            
            for level in range(n_levels):
                if level == n_levels - 1:
                    mask = channel_data >= thresholds[level]
                else:
                    mask = (channel_data >= thresholds[level]) & (channel_data < thresholds[level + 1])
                
                if len(signal_np.shape) > 1:
                    result[i][mask] = level
                else:
                    result[mask] = level
        
        discretized = torch.from_numpy(result)
        
    elif method == "zscore":
        # 基于 Z-score 的分割
        mean = signal.mean(dim=dim, keepdim=True)
        std = signal.std(dim=dim, keepdim=True)
        
        # 避免除零
        std = torch.where(std == 0, torch.ones_like(std), std)
        
        zscore = (signal - mean) / std
        
        # 创建阈值
        if n_levels == 3:
            # 三级：低(-1σ以下)，中(-1σ到1σ)，高(1σ以上)
            discretized = torch.zeros_like(signal, dtype=torch.int)
            discretized[zscore > 1.0] = 2
            discretized[(zscore >= -1.0) & (zscore <= 1.0)] = 1
            discretized[zscore < -1.0] = 0
        else:
            # 通用情况：均匀分布阈值
            thresholds = torch.linspace(-2, 2, n_levels + 1)
            discretized = torch.zeros_like(signal, dtype=torch.int)
            
            for level in range(n_levels):
                if level == n_levels - 1:
                    mask = zscore >= thresholds[level]
                else:
                    mask = (zscore >= thresholds[level]) & (zscore < thresholds[level + 1])
                discretized[mask] = level
    
    return discretized


def adaptive_binarize(
    signal: torch.Tensor, 
    window_size: int = 100,
    overlap: float = 0.5
) -> torch.Tensor:
    """自适应窗口二值化
    
    每个窗口内使用中位数阈值进行二值化
    
    Args:
        signal: 输入信号张量 (channels, time)
        window_size: 窗口大小
        overlap: 窗口重叠比例
    
    Returns:
        二值化后的信号
    """
    channels, time_steps = signal.shape
    step_size = int(window_size * (1 - overlap))
    result = torch.zeros_like(signal, dtype=torch.int)
    
    for start in range(0, time_steps - window_size + 1, step_size):
        end = start + window_size
        window = signal[:, start:end]
        
        # 每个通道独立计算中位数
        median = window.median(dim=1, keepdim=True).values
        binary_window = (window > median).int()
        
        # 处理重叠区域：使用平均值
        if start == 0:
            result[:, start:end] = binary_window
        else:
            # 重叠区域取平均（四舍五入）
            overlap_start = start
            overlap_end = min(start + int(window_size * overlap), end)
            
            if overlap_end > overlap_start:
                existing = result[:, overlap_start:overlap_end].float()
                new_vals = binary_window[:, :overlap_end-overlap_start].float()
                avg = (existing + new_vals) / 2
                result[:, overlap_start:overlap_end] = avg.round().int()
            
            # 非重叠区域直接赋值
            if overlap_end < end:
                non_overlap_start = overlap_end - start
                result[:, overlap_end:end] = binary_window[:, non_overlap_start:]
    
    return result


def complexity_aware_discretize(
    signal: torch.Tensor,
    target_complexity: float = 0.5,
    n_levels: int = 2
) -> Tuple[torch.Tensor, float]:
    """复杂度感知的离散化
    
    尝试不同的阈值，选择接近目标复杂度的离散化结果
    
    Args:
        signal: 输入信号张量
        target_complexity: 目标复杂度 (0-1)
        n_levels: 离散化级别数
    
    Returns:
        (离散化信号, 实际复杂度)
    """
    def calculate_complexity(discrete_signal):
        """计算离散信号的复杂度（基于熵）"""
        flat = discrete_signal.flatten()
        unique, counts = torch.unique(flat, return_counts=True)
        probs = counts.float() / len(flat)
        entropy = -(probs * torch.log2(probs + 1e-8)).sum()
        max_entropy = torch.log2(torch.tensor(float(n_levels)))
        return entropy / max_entropy
    
    best_discretized = None
    best_complexity = 0
    best_diff = float('inf')
    
    # 尝试不同的方法和参数
    methods = ["zscore", "uniform", "quantile"]
    
    for method in methods:
        try:
            discretized = multi_level_discretize(signal, n_levels, method)
            complexity = calculate_complexity(discretized)
            diff = abs(complexity - target_complexity)
            
            if diff < best_diff:
                best_diff = diff
                best_discretized = discretized
                best_complexity = complexity
                
        except Exception:
            continue
    
    if best_discretized is None:
        # 回退到简单二值化
        best_discretized = median_binarize(signal)
        best_complexity = calculate_complexity(best_discretized)
    
    return best_discretized, best_complexity.item()