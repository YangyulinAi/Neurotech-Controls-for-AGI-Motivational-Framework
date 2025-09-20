#!/usr/bin/env python3
"""
Concordance Correlation Coefficient (CCC) Loss Function
DFR5 Advanced Loss Functions for Emotion Recognition
"""

import torch
import torch.nn as nn
import numpy as np

class CCCLoss(nn.Module):
    """
    Concordance Correlation Coefficient Loss
    
    CCC measures both correlation and agreement between predicted and true values.
    It is particularly suitable for emotion recognition tasks where both
    direction and magnitude of predictions matter.
    
    CCC = (2 * σ_xy) / (σ_x² + σ_y² + (μ_x - μ_y)²)
    
    Where:
    - σ_xy is the covariance between x and y
    - σ_x², σ_y² are the variances of x and y
    - μ_x, μ_y are the means of x and y
    """
    
    def __init__(self, reduction='mean', epsilon=1e-8):
        """
        Initialize CCC Loss
        
        Args:
            reduction: Reduction method ('mean', 'sum', 'none')
            epsilon: Small value to prevent division by zero
        """
        super(CCCLoss, self).__init__()
        self.reduction = reduction
        self.epsilon = epsilon
    
    def forward(self, predictions, targets):
        """
        Compute CCC Loss
        
        Args:
            predictions: Model predictions (batch_size, n_outputs)
            targets: Ground truth targets (batch_size, n_outputs)
            
        Returns:
            CCC loss (scalar or tensor depending on reduction)
        """
        # Flatten tensors if needed
        if predictions.dim() > 2:
            predictions = predictions.view(predictions.size(0), -1)
        if targets.dim() > 2:
            targets = targets.view(targets.size(0), -1)
        
        # Compute means
        pred_mean = torch.mean(predictions, dim=0)
        target_mean = torch.mean(targets, dim=0)
        
        # Center the data
        pred_centered = predictions - pred_mean
        target_centered = targets - target_mean
        
        # Compute variances
        pred_var = torch.mean(pred_centered ** 2, dim=0)
        target_var = torch.mean(target_centered ** 2, dim=0)
        
        # Compute covariance
        covariance = torch.mean(pred_centered * target_centered, dim=0)
        
        # Compute CCC
        numerator = 2 * covariance
        denominator = pred_var + target_var + (pred_mean - target_mean) ** 2 + self.epsilon
        
        ccc = numerator / denominator
        
        # Convert to loss (1 - CCC)
        ccc_loss = 1 - ccc
        
        # Apply reduction
        if self.reduction == 'mean':
            return torch.mean(ccc_loss)
        elif self.reduction == 'sum':
            return torch.sum(ccc_loss)
        else:
            return ccc_loss
    
    def compute_ccc_metric(self, predictions, targets):
        """
        Compute CCC as a metric (not loss)
        
        Args:
            predictions: Model predictions
            targets: Ground truth targets
            
        Returns:
            CCC values
        """
        with torch.no_grad():
            ccc_loss = self.forward(predictions, targets)
            return 1 - ccc_loss


class MixedLoss(nn.Module):
    """
    Mixed Loss Function combining CCC and MSE
    
    This loss combines the agreement measurement of CCC with the
    magnitude penalty of MSE for robust emotion recognition.
    
    Loss = α * CCC_Loss + (1-α) * MSE_Loss
    """
    
    def __init__(self, alpha=0.7, reduction='mean'):
        """
        Initialize Mixed Loss
        
        Args:
            alpha: Weight for CCC loss (0-1), (1-alpha) for MSE
            reduction: Reduction method
        """
        super(MixedLoss, self).__init__()
        self.alpha = alpha
        self.ccc_loss = CCCLoss(reduction=reduction)
        self.mse_loss = nn.MSELoss(reduction=reduction)
    
    def forward(self, predictions, targets):
        """
        Compute Mixed Loss
        
        Args:
            predictions: Model predictions
            targets: Ground truth targets
            
        Returns:
            Mixed loss value
        """
        ccc_component = self.ccc_loss(predictions, targets)
        mse_component = self.mse_loss(predictions, targets)
        
        return self.alpha * ccc_component + (1 - self.alpha) * mse_component


def get_loss_function(loss_type='MSE', **kwargs):
    """
    Factory function to get loss function by name
    
    Args:
        loss_type: Type of loss ('MSE', 'CCC', 'mixed')
        **kwargs: Additional arguments for loss functions
        
    Returns:
        Loss function instance
    """
    if loss_type.upper() == 'MSE':
        return nn.MSELoss(**kwargs)
    elif loss_type.upper() == 'CCC':
        return CCCLoss(**kwargs)
    elif loss_type.upper() == 'MIXED':
        return MixedLoss(**kwargs)
    else:
        raise ValueError(f"Unknown loss type: {loss_type}")


# Test functions
def test_ccc_loss():
    """Test CCC loss computation"""
    print("Testing CCC Loss...")
    
    # Create sample data
    batch_size = 32
    n_outputs = 2  # valence, arousal
    
    predictions = torch.randn(batch_size, n_outputs)
    targets = predictions + 0.1 * torch.randn(batch_size, n_outputs)  # Add small noise
    
    # Test CCC loss
    ccc_loss = CCCLoss()
    loss_value = ccc_loss(predictions, targets)
    ccc_metric = ccc_loss.compute_ccc_metric(predictions, targets)
    
    print(f"CCC Loss: {loss_value.item():.4f}")
    print(f"CCC Metric: {ccc_metric.item():.4f}")
    
    # Test mixed loss
    mixed_loss = MixedLoss(alpha=0.7)
    mixed_value = mixed_loss(predictions, targets)
    
    print(f"Mixed Loss: {mixed_value.item():.4f}")
    
    # Compare with MSE
    mse_loss = nn.MSELoss()
    mse_value = mse_loss(predictions, targets)
    
    print(f"MSE Loss: {mse_value.item():.4f}")
    
    print("✓ CCC Loss test completed")


if __name__ == "__main__":
    test_ccc_loss()