#!/usr/bin/env python3
"""
Training script for labeled EEG data with subject-based organization
Reads labels.json files from subject directories and trains with true emotion labels
"""

import argparse
import json
import os
import sys
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import LeaveOneGroupOut, StratifiedKFold, KFold
import scipy.io
import matplotlib.pyplot as plt
import time
import requests
import yaml

# Add parent directory to path for imports - place at beginning to override system packages
scripts_dir = str(Path(__file__).parent.parent)
sys.path.insert(0, scripts_dir)
train_dir = str(Path(__file__).parent)
sys.path.insert(0, train_dir)

# 导入 IIT Φ 计算器
try:
    from phi_estimator import PhiEstimator
    PHI_AVAILABLE = True
    print("✓ IIT Φ 计算器模块加载成功")
except ImportError as e:
    PHI_AVAILABLE = False
    print(f"警告: IIT Φ 计算器不可用 ({e})，将跳过 Φ 计算功能")

from model_cnn_tcn import EmotionNet
from preprocess import extract_feats

def concordance_correlation_coefficient(y_true, y_pred):
    """Compute Concordance Correlation Coefficient"""
    x = y_true.flatten()
    y = y_pred.flatten()
    
    mean_x = torch.mean(x)
    mean_y = torch.mean(y)
    var_x = torch.var(x, unbiased=False)
    var_y = torch.var(y, unbiased=False)
    cov_xy = torch.mean((x - mean_x) * (y - mean_y))
    
    # Add small epsilon for numerical stability
    eps = 1e-8
    ccc = (2 * cov_xy) / (var_x + var_y + (mean_x - mean_y)**2 + eps)
    return ccc

def ccc_loss(pred, gold):
    """CCC Loss function (1 - CCC to minimize)"""
    return 1 - concordance_correlation_coefficient(gold, pred)

def mixed_loss(pred, gold, alpha=0.7):
    """Mixed CCC and MSE loss"""
    mse = nn.MSELoss()(pred, gold)
    ccc_l = ccc_loss(pred, gold)
    return alpha * ccc_l + (1 - alpha) * mse

def mse_loss(pred, gold):
    """Mean Squared Error loss"""
    return nn.MSELoss()(pred, gold)

class LabeledEEGDataset(Dataset):
    """
    Dataset class for labeled EEG data organized by subjects
    """
    def __init__(self, subject_dirs, window_size=5, overlap=0.5, fs=256, training=True):
        """
        Args:
            subject_dirs: List of subject directory paths
            window_size: Window size in seconds for segmentation
            overlap: Overlap ratio between windows (0-1)
            fs: Sampling frequency
            training: If True, apply data augmentation during __getitem__
        """
        self.subject_dirs = subject_dirs
        self.window_size = window_size
        self.overlap = overlap
        self.fs = fs
        self.training = training
        self.window_samples = int(window_size * fs)
        self.step_samples = int(self.window_samples * (1 - overlap))
        
        self.windows = []
        self.labels = []
        
        self._load_all_subjects()
    
    def _load_all_subjects(self):
        """Load data from all subject directories"""
        print(f"Loading data from {len(self.subject_dirs)} subjects...")
        
        for subject_dir in self.subject_dirs:
            subject_path = Path(subject_dir)
            labels_path = subject_path / 'labels.json'
            
            if not labels_path.exists():
                print(f"Warning: No labels.json found in {subject_path}")
                continue
            
            # Load labels
            with open(labels_path, 'r') as f:
                labels_data = json.load(f)
            
            subject_id = labels_data.get('subject_id', subject_path.name)
            print(f"Processing subject {subject_id}...")
            
            # Process each labeled file
            file_labels = labels_data.get('files', {})
            for filename, file_info in file_labels.items():
                file_path = subject_path / filename
                
                if not file_path.exists():
                    print(f"Warning: File {filename} not found in {subject_path}")
                    continue
                
                if not filename.endswith('.set'):
                    print(f"Skipping non-SET file: {filename}")
                    continue
                
                # Extract valence and arousal labels
                valence = file_info.get('valence', 0.0)
                arousal = file_info.get('arousal', 0.0)
                
                print(f"  Loading {filename} (valence={valence:.3f}, arousal={arousal:.3f})")
                
                # Load and process EEG data
                try:
                    windows, labels = self._process_set_file(file_path, valence, arousal)
                    self.windows.extend(windows)
                    self.labels.extend(labels)
                    print(f"    Created {len(windows)} windows")
                except Exception as e:
                    print(f"    Error processing {filename}: {e}")
                    continue
        
        print(f"Total windows created: {len(self.windows)}")
        print(f"Label statistics:")
        if self.labels:
            labels_array = np.array(self.labels)
            print(f"  Valence range: [{labels_array[:, 0].min():.3f}, {labels_array[:, 0].max():.3f}]")
            print(f"  Arousal range: [{labels_array[:, 1].min():.3f}, {labels_array[:, 1].max():.3f}]")
    
    def _process_set_file(self, set_file_path, valence, arousal):
        """Process a single SET file and create windows"""
        # Load .set file
        mat_data = scipy.io.loadmat(str(set_file_path), struct_as_record=False, squeeze_me=True)
        
        # Extract EEG data
        eeg_data = None
        if hasattr(mat_data.get('data'), 'shape'):
            eeg_data = mat_data['data']
        else:
            # Try to find EEG data in the structure
            for key, value in mat_data.items():
                if hasattr(value, 'shape') and value.ndim == 2:
                    eeg_data = value
                    break
        
        if eeg_data is None:
            raise ValueError("Could not find EEG data in SET file")
        
        # Ensure correct orientation (channels x time)
        if eeg_data.shape[0] > eeg_data.shape[1]:
            eeg_data = eeg_data.T
        
        n_channels, n_times = eeg_data.shape
        
        # Create windows
        windows = []
        labels = []
        
        n_windows = (n_times - self.window_samples) // self.step_samples + 1
        
        for i in range(n_windows):
            start_idx = i * self.step_samples
            end_idx = start_idx + self.window_samples
            
            if end_idx > n_times:
                break
            
            window_data = eeg_data[:, start_idx:end_idx]
            
            try:
                # Extract features
                spec, de = extract_feats(window_data, self.fs)
                
                # Resize spectrogram to 224x224
                from scipy.ndimage import zoom
                if spec.shape[1:] != (224, 224):
                    spec_resized = np.zeros((3, 224, 224), dtype=np.float32)
                    for c in range(3):
                        zoom_h = 224 / spec.shape[1]
                        zoom_w = 224 / spec.shape[2]
                        spec_resized[c] = zoom(spec[c], (zoom_h, zoom_w), order=1)
                    spec = spec_resized
                
                windows.append((spec, de))
                labels.append([valence, arousal])
                
            except Exception as e:
                print(f"      Warning: Failed to extract features for window {i}: {e}")
                continue
        
        return windows, labels
    
    def __len__(self):
        return len(self.windows)
    
    def __getitem__(self, idx):
        spec, de = self.windows[idx]
        label = self.labels[idx]
        
        # Apply EEG-friendly data augmentation during training
        if self.training:
            spec, de = self._apply_eeg_augmentation(spec, de)
        
        return (
            torch.FloatTensor(spec),      # Shape: (3, 224, 224)
            torch.FloatTensor(de),        # Shape: (26,)
            torch.FloatTensor(label)      # Shape: (2,) [valence, arousal]
        )
    
    def _apply_eeg_augmentation(self, spec, de):
        """Apply EEG-friendly data augmentation techniques"""
        import random
        
        spec = spec.copy()
        de = de.copy()
        
        # 1. Channel dropout (randomly zero out 1-2 channels in DE features)
        if random.random() < 0.3:
            num_channels_to_drop = random.randint(1, 2)
            channels_to_drop = random.sample(range(len(de)), num_channels_to_drop)
            de[channels_to_drop] = 0
        
        # 2. Amplitude jittering (add small gaussian noise to DE features)
        if random.random() < 0.4:
            noise_std = 0.05 * np.std(de)  # 5% of signal std
            noise = np.random.normal(0, noise_std, de.shape)
            de = de + noise
        
        # 3. Spectral masking (randomly mask small patches in spectrogram)
        if random.random() < 0.3:
            # Frequency masking
            freq_mask_size = random.randint(5, 15)
            freq_start = random.randint(0, spec.shape[1] - freq_mask_size)
            spec[:, freq_start:freq_start+freq_mask_size, :] *= 0.1
            
            # Time masking
            time_mask_size = random.randint(5, 15)
            time_start = random.randint(0, spec.shape[2] - time_mask_size)
            spec[:, :, time_start:time_start+time_mask_size] *= 0.1
        
        # 4. Time-domain jittering (circular shift in spectrogram time axis)
        if random.random() < 0.3:
            time_shift = random.randint(-10, 10)  # Shift by up to ±10 time bins
            if time_shift != 0:
                spec = np.roll(spec, time_shift, axis=2)  # Roll along time axis
        
        # 5. Amplitude scaling (randomly scale overall amplitude)
        if random.random() < 0.2:
            scale_factor = random.uniform(0.8, 1.2)
            spec = spec * scale_factor
            de = de * scale_factor
        
        return spec, de

def train_single_fold(args, train_dataset, val_dataset, device, fold_id=1, val_subject=""):
    """Train a single fold for cross-validation"""
    from torch.utils.data import DataLoader
    import torch.nn as nn
    import time
    from model_cnn_tcn import EmotionNet
    
    # Create data loaders
    train_loader = DataLoader(
        train_dataset, 
        batch_size=args.batch_size, 
        shuffle=True,
        drop_last=True,
        num_workers=0
    )
    
    val_loader = DataLoader(
        val_dataset, 
        batch_size=args.batch_size, 
        shuffle=False,
        drop_last=False,
        num_workers=0
    )
    
    # Initialize model
    model = EmotionNet(dropout_rate=args.dropout_rate, use_batch_norm=args.use_batch_norm).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-3)  # Increased weight decay
    
    # Use CosineAnnealing with warm restarts for better convergence
    scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(
        optimizer, T_0=max(5, args.epochs//3), T_mult=2, eta_min=1e-6  # Ensure T_0 >= 5
    )
    
    # Loss function setup
    if args.loss_fn == 'CCC':
        criterion = ccc_loss
    elif args.loss_fn == 'mixed':
        criterion = lambda pred, target: mixed_loss(pred, target, alpha=args.loss_alpha)
    else:
        criterion = nn.MSELoss()
    
    # Training loop for this fold
    best_val_loss = float('inf')
    for epoch in range(args.epochs):
        model.train()
        train_loss = 0
        
        for batch_idx, (spec, de, labels) in enumerate(train_loader):
            spec, de = spec.to(device), de.to(device)
            targets = labels.to(device)  # labels is already (batch_size, 2)
            
            optimizer.zero_grad()
            pred = model(spec, de)
            loss = criterion(pred, targets)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        # Validation
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for spec, de, labels in val_loader:
                spec, de = spec.to(device), de.to(device)
                targets = labels.to(device)  # labels is already (batch_size, 2)
                pred = model(spec, de)
                loss = criterion(pred, targets)
                val_loss += loss.item()
        
        train_loss /= len(train_loader)
        val_loss /= len(val_loader)
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
        
        scheduler.step()  # CosineAnnealingWarmRestarts doesn't use val_loss
        
        if epoch % 5 == 0:
            print(f"  Fold {fold_id} E{epoch+1}/{args.epochs}: train={train_loss:.4f}, val={val_loss:.4f}")
    
    return {
        'fold_id': fold_id,
        'val_subject': val_subject,
        'train_loss': train_loss,
        'val_loss': best_val_loss
    }


def train(args):
    """Main training function"""
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f'Using device: {device}')
    
    # Get subject directories
    training_dir = Path(args.data_dir)
    if not training_dir.exists():
        raise ValueError(f"Training directory not found: {args.data_dir}")
    
    # Find all subject directories
    subject_dirs = []
    for item in training_dir.iterdir():
        if item.is_dir() and item.name.startswith('s') and item.name[1:].isdigit():
            labels_path = item / 'labels.json'
            if labels_path.exists():
                subject_dirs.append(str(item))
            else:
                print(f"Warning: Subject {item.name} has no labels.json, skipping")
    
    if not subject_dirs:
        raise ValueError(f"No valid subject directories with labels.json found in {args.data_dir}")
    
    print(f"Found {len(subject_dirs)} subjects with labels: {[Path(d).name for d in subject_dirs]}")
    
    # Create dataset
    dataset = LabeledEEGDataset(
        subject_dirs=subject_dirs,
        window_size=args.window_size,
        overlap=args.overlap,
        fs=256
    )
    
    if len(dataset) == 0:
        raise ValueError("No training data found")
    
    print(f"Dataset size: {len(dataset)} windows")
    
    # Handle cross-validation splits
    if args.cv_method == 'LOSO' and len(subject_dirs) > 1:
        print(f"Using LOSO cross-validation with {len(subject_dirs)} subjects")
        # LOSO: Leave-One-Subject-Out to prevent data leakage
        all_results = []
        for i, val_subject_dir in enumerate(subject_dirs):
            val_subject_name = Path(val_subject_dir).name
            train_subject_dirs = [d for d in subject_dirs if d != val_subject_dir]
            
            print(f"\n=== LOSO Fold {i+1}/{len(subject_dirs)} ===")
            print(f"Validation Subject: {val_subject_name}")
            print(f"Training Subjects: {[Path(d).name for d in train_subject_dirs]}")
            
            # Create separate datasets for this fold
            train_dataset_fold = LabeledEEGDataset(
                subject_dirs=train_subject_dirs,
                window_size=args.window_size,
                overlap=args.overlap,
                fs=256,
                training=True  # Enable augmentation for training
            )
            val_dataset_fold = LabeledEEGDataset(
                subject_dirs=[val_subject_dir],
                window_size=args.window_size,
                overlap=args.overlap,
                fs=256,
                training=False  # Disable augmentation for validation
            )
            
            print(f"Train windows: {len(train_dataset_fold)}, Val windows: {len(val_dataset_fold)}")
            
            # Train model for this fold
            fold_result = train_single_fold(
                args, train_dataset_fold, val_dataset_fold, 
                device, fold_id=i+1, val_subject=val_subject_name
            )
            all_results.append(fold_result)
        
        # Report LOSO results
        avg_train_loss = sum(r['train_loss'] for r in all_results) / len(all_results)
        avg_val_loss = sum(r['val_loss'] for r in all_results) / len(all_results)
        print(f"\n=== LOSO Results Summary ===")
        print(f"Average Train Loss: {avg_train_loss:.4f}")
        print(f"Average Validation Loss: {avg_val_loss:.4f}")
        for i, result in enumerate(all_results):
            print(f"  Fold {i+1} ({result['val_subject']}): train={result['train_loss']:.4f}, val={result['val_loss']:.4f}")
        return
    else:
        # Standard train/validation split (group-aware to prevent leakage)
        if len(subject_dirs) > 1:
            # Group-aware split: keep subjects together
            val_subjects = subject_dirs[:max(1, len(subject_dirs)//5)]  # 20% subjects for validation
            train_subjects = subject_dirs[len(val_subjects):]
            
            train_dataset = LabeledEEGDataset(
                subject_dirs=train_subjects,
                window_size=args.window_size,
                overlap=args.overlap,
                fs=256,
                training=True  # Enable augmentation for training
            )
            val_dataset = LabeledEEGDataset(
                subject_dirs=val_subjects,
                window_size=args.window_size,
                overlap=args.overlap,
                fs=256,
                training=False  # Disable augmentation for validation
            )
            print(f"Group-aware split - Train subjects: {[Path(d).name for d in train_subjects]}")
            print(f"Group-aware split - Val subjects: {[Path(d).name for d in val_subjects]}")
        else:
            # Single subject: random split within subject
            train_size = int(0.8 * len(dataset))
            val_size = len(dataset) - train_size
            train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])
            # Fix validation augmentation for single subject (safer approach)
            try:
                val_dataset.dataset.training = False  # Disable augmentation for validation
                print("Single subject: using random split (validation augmentation disabled)")
            except AttributeError:
                print("Single subject: using random split (validation augmentation may still be enabled)")
    
    # Create data loaders with drop_last=True to avoid BatchNorm issues
    train_loader = DataLoader(
        train_dataset, 
        batch_size=args.batch_size, 
        shuffle=True,
        drop_last=True,  # Drop incomplete batches to avoid BatchNorm issues
        num_workers=0  # Avoid multiprocessing issues
    )
    
    val_loader = DataLoader(
        val_dataset, 
        batch_size=args.batch_size, 
        shuffle=False,
        drop_last=False,  # Keep all validation data
        num_workers=0
    )
    
    print(f"Training set: {len(train_dataset)} windows")
    print(f"Validation set: {len(val_dataset)} windows")
    
    # Initialize model with dropout and batch norm
    model = EmotionNet(dropout_rate=args.dropout_rate, use_batch_norm=args.use_batch_norm).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-3)  # Consistent with train_single_fold
    
    # Use CosineAnnealing with warm restarts for better convergence (consistent with train_single_fold)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(
        optimizer, T_0=max(5, args.epochs//3), T_mult=2, eta_min=1e-6  # Ensure T_0 >= 5
    )
    
    # 初始化 Φ 计算器（如果启用）
    phi_estimator = None
    if args.compute_phi and PHI_AVAILABLE:
        try:
            # 加载配置文件（如果存在）
            phi_config = {}
            if os.path.exists(args.phi_config):
                with open(args.phi_config, 'r') as f:
                    phi_config = yaml.safe_load(f)
            
            phi_estimator = PhiEstimator(
                method=args.phi_method,
                max_channels=args.phi_max_channels,
                **phi_config
            )
            print(f"✓ IIT Φ 计算器已启用: {phi_estimator.get_info()}")
        except Exception as e:
            print(f"⚠️ Φ 计算器初始化失败: {e}")
            phi_estimator = None
    elif args.compute_phi and not PHI_AVAILABLE:
        print("⚠️ 请求启用 Φ 计算，但模块不可用，将跳过")

    # Training loop
    print(f"Starting training for {args.epochs} epochs...")
    print(f"Batch size: {args.batch_size}, Learning rate: {args.lr}")
    print(f"Window size: {args.window_size}s, Overlap: {args.overlap}")
    print(f"Φ 计算: {'启用' if phi_estimator else '禁用'}")
    
    best_loss = float('inf')
    patience_counter = 0
    
    # Training visualization data
    train_losses = []
    epoch_times = []
    learning_rates = []
    
    for epoch in range(args.epochs):
        epoch_start_time = time.time()
        model.train()
        total_loss = 0.0
        batch_losses = []
        
        for batch_idx, (spec, de, labels) in enumerate(train_loader):
            spec = spec.to(device)
            de = de.to(device)
            labels = labels.to(device)
            
            optimizer.zero_grad()
            pred = model(spec, de)
            
            # Use specified loss function
            if args.loss_fn == 'CCC':
                loss = ccc_loss(pred, labels)
            elif args.loss_fn == 'mixed':
                loss = mixed_loss(pred, labels, alpha=args.loss_alpha)
            else:  # MSE
                loss = mse_loss(pred, labels)
            
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            
            batch_loss = loss.item()
            batch_losses.append(batch_loss)
            
            total_loss += batch_loss
            
            if batch_idx % 10 == 0:
                print(f"E{epoch+1}/{args.epochs} Batch {batch_idx}/{len(train_loader)} loss={batch_loss:.4f}")
        
        # Training metrics
        train_loss = total_loss / len(train_loader)
        
        # Validation step
        model.eval()
        val_total_loss = 0.0
        val_loss = 0.0  # Default value for empty validation set
        
        # Check if validation loader has data to prevent division by zero
        if len(val_loader) > 0:
            with torch.no_grad():
                for spec, de, labels in val_loader:
                    spec = spec.to(device)
                    de = de.to(device)
                    labels = labels.to(device)
                    
                    pred = model(spec, de)
                    
                    # Use same loss function as training
                    if args.loss_fn == 'CCC':
                        loss = ccc_loss(pred, labels)
                    elif args.loss_fn == 'mixed':
                        loss = mixed_loss(pred, labels, alpha=args.loss_alpha)
                    else:  # MSE
                        loss = mse_loss(pred, labels)
                    
                    val_total_loss += loss.item()
            
            val_loss = val_total_loss / len(val_loader)
        else:
            print("Warning: Empty validation set, using training loss for validation")
        epoch_time = time.time() - epoch_start_time
        current_lr = optimizer.param_groups[0]['lr']
        
        # Store training metrics
        train_losses.append(train_loss)
        epoch_times.append(epoch_time)
        learning_rates.append(current_lr)
        
        progress_pct = ((epoch + 1) / args.epochs) * 100
        print(f"E{epoch+1}/{args.epochs} train_loss={train_loss:.4f} val_loss={val_loss:.4f} time={epoch_time:.1f}s lr={current_lr:.6f}")
        print(f"=== PROGRESS: {progress_pct:.1f}% COMPLETE ({epoch+1}/{args.epochs} epochs) ===")
        print(f"Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Best Val Loss: {best_loss:.4f}")
        sys.stdout.flush()  # Force immediate output
        
        # 计算 Φ 值（如果启用）
        phi_values = None
        if phi_estimator is not None:
            try:
                # 从最后一个批次获取原始 EEG 数据进行 Φ 计算
                # 注意：这里是示例，实际应用中可能需要从数据集中获取原始 EEG
                sample_batch = spec[:min(4, spec.size(0))]  # 取少量样本避免计算过载
                phi_values = phi_estimator.compute(sample_batch)
                avg_phi = phi_values.mean().item() if len(phi_values) > 0 else 0.0
                print(f"      Φ = {avg_phi:.6f} (样本数: {len(phi_values)})")
            except Exception as e:
                print(f"      Φ 计算失败: {e}")
                avg_phi = 0.0

        # Update learning rate scheduler (CosineAnnealingWarmRestarts doesn't use val_loss)
        scheduler.step()
        
        # Send training progress to frontend
        try:
            progress_data = {
                "type": "training_progress",
                "epoch": epoch + 1,
                "total_epochs": args.epochs,
                "loss": val_loss,  # Use validation loss for frontend
                "train_loss": train_loss,
                "val_loss": val_loss,
                "best_loss": best_loss,
                "learning_rate": current_lr,
                "epoch_time": epoch_time,
                "progress_percentage": ((epoch + 1) / args.epochs) * 100
            }
            
            # 添加 Φ 值（如果可用）
            if phi_values is not None:
                progress_data["phi"] = avg_phi
                
            requests.post('http://localhost:5000/api/bci/broadcast', 
                         json=progress_data, timeout=1)
        except:
            pass  # Ignore if can't send to frontend
        
        # Save best model based on validation loss
        if val_loss < best_loss:
            best_loss = val_loss
            patience_counter = 0
            torch.save(model.state_dict(), args.checkpoint_path)
            print(f"New best model saved! Val Loss: {best_loss:.4f}")
        else:
            patience_counter += 1
        
        # Learning rate scheduling (already done above with val_loss)
        
        # Early stopping
        if patience_counter >= 10:
            print(f"Early stopping triggered at epoch {epoch+1}")
            break
    
    print(f"Training completed. Best loss: {best_loss:.4f}")
    
    # Create training visualization
    create_training_plots(train_losses, epoch_times, learning_rates, args.checkpoint_path)
    
    # Export to ONNX
    print("Exporting to ONNX...")
    model.load_state_dict(torch.load(args.checkpoint_path))
    model.eval()
    
    # Create dummy inputs
    dummy_spec = torch.randn(1, 3, 224, 224).to(device)
    dummy_de = torch.randn(1, 26).to(device)
    
    torch.onnx.export(
        model,
        (dummy_spec, dummy_de),
        args.onnx_path,
        export_params=True,
        opset_version=11,
        do_constant_folding=True,
        input_names=['spec', 'de'],
        output_names=['valence_arousal'],
        dynamic_axes={
            'spec': {0: 'batch_size'},
            'de': {0: 'batch_size'},
            'valence_arousal': {0: 'batch_size'}
        }
    )
    print(f"ONNX exported to {args.onnx_path}")

def create_training_plots(train_losses, epoch_times, learning_rates, checkpoint_path):
    """Create and save training visualization plots"""
    print("Creating training visualization plots...")
    
    # Set up the plotting style
    plt.style.use('default')
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    epochs = range(1, len(train_losses) + 1)
    
    # Plot 1: Training Loss
    ax1.plot(epochs, train_losses, 'b-', linewidth=2, label='Training Loss')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('MSE Loss')
    ax1.set_title('Training Loss Over Time')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Plot 2: Learning Rate
    ax2.plot(epochs, learning_rates, 'r-', linewidth=2, label='Learning Rate')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Learning Rate')
    ax2.set_title('Learning Rate Schedule')
    ax2.set_yscale('log')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Plot 3: Training Time per Epoch
    ax3.bar(epochs, epoch_times, alpha=0.7, color='green', label='Epoch Time')
    ax3.set_xlabel('Epoch')
    ax3.set_ylabel('Time (seconds)')
    ax3.set_title('Training Time per Epoch')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # Plot 4: Loss Improvement
    if len(train_losses) > 1:
        loss_improvements = []
        for i in range(1, len(train_losses)):
            improvement = train_losses[i-1] - train_losses[i]
            loss_improvements.append(improvement)
        
        ax4.plot(range(2, len(train_losses) + 1), loss_improvements, 'purple', 
                linewidth=2, marker='o', markersize=4, label='Loss Improvement')
        ax4.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        ax4.set_xlabel('Epoch')
        ax4.set_ylabel('Loss Improvement')
        ax4.set_title('Loss Improvement per Epoch')
        ax4.grid(True, alpha=0.3)
        ax4.legend()
    else:
        ax4.text(0.5, 0.5, 'Not enough data\nfor loss improvement', 
                ha='center', va='center', transform=ax4.transAxes)
        ax4.set_title('Loss Improvement per Epoch')
    
    plt.tight_layout()
    
    # Save the plot
    plot_path = checkpoint_path.replace('.pt', '_training_plots.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Training plots saved to: {plot_path}")
    
    # Create summary statistics
    create_training_summary(train_losses, epoch_times, learning_rates, checkpoint_path)

def create_training_summary(train_losses, epoch_times, learning_rates, checkpoint_path):
    """Create and save training summary statistics"""
    summary = {
        "training_completed": True,
        "total_epochs": len(train_losses),
        "final_loss": float(train_losses[-1]) if train_losses else 0.0,
        "best_loss": float(min(train_losses)) if train_losses else 0.0,
        "total_training_time": float(sum(epoch_times)) if epoch_times else 0.0,
        "average_epoch_time": float(np.mean(epoch_times)) if epoch_times else 0.0,
        "initial_lr": float(learning_rates[0]) if learning_rates else 0.0,
        "final_lr": float(learning_rates[-1]) if learning_rates else 0.0,
        "loss_reduction": float(train_losses[0] - train_losses[-1]) if len(train_losses) > 1 else 0.0,
        "loss_reduction_percentage": float((train_losses[0] - train_losses[-1]) / train_losses[0] * 100) if len(train_losses) > 1 and train_losses[0] > 0 else 0.0
    }
    
    # Save summary as JSON
    summary_path = checkpoint_path.replace('.pt', '_training_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary to console
    print("\n" + "="*50)
    print("TRAINING SUMMARY")
    print("="*50)
    print(f"Total Epochs: {summary['total_epochs']}")
    print(f"Best Loss: {summary['best_loss']:.6f}")
    print(f"Final Loss: {summary['final_loss']:.6f}")
    print(f"Loss Reduction: {summary['loss_reduction']:.6f} ({summary['loss_reduction_percentage']:.1f}%)")
    print(f"Total Training Time: {summary['total_training_time']:.1f} seconds")
    print(f"Average Epoch Time: {summary['average_epoch_time']:.1f} seconds")
    print(f"Learning Rate: {summary['initial_lr']:.6f} → {summary['final_lr']:.6f}")
    print("="*50)
    print(f"Summary saved to: {summary_path}")
    print("="*50)

def parse_args():
    parser = argparse.ArgumentParser(description='Train EEG emotion model with labeled data')
    parser.add_argument('--data_dir', type=str, default='data/training set',
                        help='Directory containing subject folders')
    parser.add_argument('--epochs', type=int, default=30,
                        help='Number of training epochs')
    parser.add_argument('--batch_size', type=int, default=16,
                        help='Batch size for training')
    parser.add_argument('--lr', type=float, default=1e-4,
                        help='Learning rate')
    parser.add_argument('--window_size', type=float, default=5.0,
                        help='Window size in seconds')
    parser.add_argument('--overlap', type=float, default=0.5,
                        help='Overlap ratio between windows')
    parser.add_argument('--checkpoint_path', type=str, default='model/model_weight/ckpt.pt',
                        help='Path to save the best model checkpoint')
    parser.add_argument('--onnx_path', type=str, default='model/model_onnx/va_regressor.onnx',
                        help='Path to save ONNX model')
    
    # DFR5 Enhancement Arguments
    parser.add_argument('--device_name', default='Standard_10_20', 
                        help='EEG device name for adapter')
    parser.add_argument('--loss_fn', default='MSE', choices=['MSE', 'CCC', 'mixed'], 
                        help='Loss function to use')
    parser.add_argument('--cv_method', default=None, choices=['LOSO', 'kfold'], 
                        help='Cross-validation method')
    parser.add_argument('--cv_folds', type=int, default=5, 
                        help='Number of folds for k-fold CV')
    parser.add_argument('--compute_phi', action='store_true', 
                        help='Compute IIT Φ values during training')
    parser.add_argument('--phi_method', default='mock', choices=['mock', 'IIT3.0', 'IIT4.0_light'], 
                        help='Φ computation method')
    parser.add_argument('--phi_max_channels', type=int, default=8, 
                        help='Maximum channels for Φ computation')
    parser.add_argument('--phi_config', default='configs/phi.yaml', 
                        help='Φ configuration file path')
    parser.add_argument('--use_batch_norm', action='store_true', 
                        help='Use batch normalization in model')
    parser.add_argument('--dropout_rate', type=float, default=0.2, 
                        help='Dropout rate (0.0 to disable, recommended: 0.2)')
    parser.add_argument('--log_dir', default='runs', 
                        help='TensorBoard log directory')
    parser.add_argument('--loss_alpha', type=float, default=0.7,
                        help='Alpha parameter for mixed loss (CCC weight)')
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    print("Training arguments:")
    print(vars(args))
    train(args)