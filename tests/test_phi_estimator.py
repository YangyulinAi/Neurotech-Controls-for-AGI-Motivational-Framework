"""
测试 IIT Φ 计算器
"""

import pytest
import torch
import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from phi_estimator import PhiEstimator
from utils.binning import (
    median_binarize, 
    threshold_binarize, 
    multi_level_discretize,
    adaptive_binarize,
    complexity_aware_discretize
)


class TestPhiEstimator:
    """PhiEstimator 测试类"""

    def test_mock_phi(self):
        """测试 mock 模式"""
        est = PhiEstimator(method="mock")
        dummy = torch.randn(4, 8, 128)  # (batch, channels, time)
        phi = est.compute(dummy)
        
        assert phi.shape == (4,)
        assert torch.all(phi == 0)
        assert est.is_available()

    def test_estimator_info(self):
        """测试计算器信息获取"""
        est = PhiEstimator(method="mock", max_channels=6, tau=2)
        info = est.get_info()
        
        assert info["method"] == "mock"
        assert info["max_channels"] == 6
        assert info["tau"] == 2
        assert info["available"] is True

    def test_different_methods(self):
        """测试不同的计算方法初始化"""
        methods = ["mock", "IIT3.0", "IIT4.0_light"]
        
        for method in methods:
            est = PhiEstimator(method=method)
            dummy = torch.randn(2, 4, 64)
            phi = est.compute(dummy)
            
            assert phi.shape == (2,)
            assert isinstance(phi, torch.Tensor)

    def test_channel_limit(self):
        """测试通道数限制"""
        est = PhiEstimator(method="mock", max_channels=4)
        
        # 测试超过最大通道数的情况
        large_input = torch.randn(1, 16, 32)  # 16 通道
        phi = est.compute(large_input)
        
        assert phi.shape == (1,)

    def test_binarization_methods(self):
        """测试不同的二值化方法"""
        bin_methods = ["median", "threshold", "multi"]
        
        for bin_method in bin_methods:
            est = PhiEstimator(method="mock", bin_method=bin_method)
            dummy = torch.randn(2, 6, 64)
            
            # 测试二值化函数
            binarized = est._binarize(dummy[0])  # 取第一个样本
            
            assert binarized.shape == (6, 64)
            assert binarized.dtype == torch.int32 or binarized.dtype == torch.int64

    def test_empty_input(self):
        """测试空输入"""
        est = PhiEstimator(method="mock")
        empty_input = torch.empty(0, 8, 128)
        phi = est.compute(empty_input)
        
        assert phi.shape == (0,)

    def test_single_sample(self):
        """测试单样本输入"""
        est = PhiEstimator(method="mock")
        single_sample = torch.randn(1, 8, 128)
        phi = est.compute(single_sample)
        
        assert phi.shape == (1,)
        assert phi.item() == 0.0


class TestBinningUtils:
    """二值化工具测试类"""

    def test_median_binarize(self):
        """测试中位数二值化"""
        signal = torch.tensor([[1.0, 2.0, 3.0, 4.0, 5.0]])
        result = median_binarize(signal, dim=-1)
        
        # 中位数是 3.0，所以 4.0, 5.0 应该是 1，其他是 0
        expected = torch.tensor([[0, 0, 0, 1, 1]])
        assert torch.equal(result, expected)

    def test_threshold_binarize(self):
        """测试阈值二值化"""
        signal = torch.tensor([[-1.0, 0.0, 1.0, 2.0]])
        result = threshold_binarize(signal, threshold=0.5)
        
        expected = torch.tensor([[0, 0, 1, 1]])
        assert torch.equal(result, expected)

    def test_multi_level_discretize(self):
        """测试多级离散化"""
        signal = torch.randn(2, 100)
        
        methods = ["uniform", "zscore"]
        for method in methods:
            result = multi_level_discretize(signal, n_levels=3, method=method)
            
            assert result.shape == signal.shape
            assert result.min() >= 0
            assert result.max() <= 2

    def test_adaptive_binarize(self):
        """测试自适应二值化"""
        signal = torch.randn(4, 200)
        result = adaptive_binarize(signal, window_size=50, overlap=0.3)
        
        assert result.shape == signal.shape
        assert result.dtype in [torch.int32, torch.int64]
        assert set(result.unique().tolist()).issubset({0, 1})

    def test_complexity_aware_discretize(self):
        """测试复杂度感知离散化"""
        signal = torch.randn(3, 150)
        result, complexity = complexity_aware_discretize(
            signal, target_complexity=0.7, n_levels=2
        )
        
        assert result.shape == signal.shape
        assert 0.0 <= complexity <= 1.0
        assert isinstance(complexity, float)

    def test_edge_cases(self):
        """测试边界情况"""
        # 常数信号
        constant_signal = torch.ones(2, 50)
        result = median_binarize(constant_signal)
        # 所有值都等于中位数，应该都是 0
        assert torch.all(result == 0)
        
        # 单一样本
        single_sample = torch.randn(1, 1)
        result = threshold_binarize(single_sample)
        assert result.shape == (1, 1)


class TestIntegration:
    """集成测试"""

    def test_phi_with_real_eeg_shape(self):
        """使用真实 EEG 数据形状测试"""
        # 模拟真实 EEG 数据：62 通道，5 秒 @ 250Hz
        batch_size = 8
        channels = 62
        time_samples = 1250  # 5 秒 * 250 Hz
        
        eeg_data = torch.randn(batch_size, channels, time_samples)
        
        est = PhiEstimator(method="mock", max_channels=8)
        phi_values = est.compute(eeg_data)
        
        assert phi_values.shape == (batch_size,)
        assert torch.all(phi_values == 0)  # mock 模式应返回 0

    def test_phi_computation_pipeline(self):
        """测试完整的 Φ 计算流水线"""
        # 创建测试数据
        eeg_batch = torch.randn(3, 6, 100)
        
        # 初始化计算器
        est = PhiEstimator(
            method="mock",
            max_channels=6,
            bin_method="median"
        )
        
        # 计算 Φ 值
        phi_values = est.compute(eeg_batch)
        
        # 验证结果
        assert isinstance(phi_values, torch.Tensor)
        assert phi_values.shape == (3,)
        assert phi_values.dtype == torch.float32

    def test_performance_benchmark(self):
        """简单的性能基准测试"""
        import time
        
        # 较大的批次
        large_batch = torch.randn(32, 16, 500)
        est = PhiEstimator(method="mock", max_channels=8)
        
        start_time = time.time()
        phi_values = est.compute(large_batch)
        end_time = time.time()
        
        computation_time = end_time - start_time
        
        assert phi_values.shape == (32,)
        assert computation_time < 1.0  # mock 模式应该很快
        print(f"Mock computation time for 32 samples: {computation_time:.4f}s")


if __name__ == "__main__":
    # 运行基本测试
    test_phi = TestPhiEstimator()
    test_phi.test_mock_phi()
    print("✓ Mock Φ 计算测试通过")
    
    test_phi.test_estimator_info()
    print("✓ 计算器信息测试通过")
    
    test_binning = TestBinningUtils()
    test_binning.test_median_binarize()
    print("✓ 中位数二值化测试通过")
    
    test_integration = TestIntegration()
    test_integration.test_phi_with_real_eeg_shape()
    print("✓ EEG 数据形状测试通过")
    
    test_integration.test_performance_benchmark()
    print("✓ 性能基准测试通过")
    
    print("\n🎉 所有测试通过！IIT Φ 计算功能已准备就绪")