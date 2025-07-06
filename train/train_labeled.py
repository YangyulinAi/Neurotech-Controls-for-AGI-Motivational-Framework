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
import scipy.io

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from model_cnn_tcn import EmotionNet
from src.preprocess import extract_feats

def ccc(pred, gold):
    """Concordance Correlation Coefficient loss"""
    pred_mean = torch.mean(pred, dim=0)
    gold_mean = torch.mean(gold, dim=0)
    
    pred_var = torch.var(pred, dim=0)
    gold_var = torch.var(gold, dim=0)
    
    covariance = torch.mean((pred - pred_mean) * (gold - gold_mean), dim=0)
    
    ccc_val = (2 * covariance) / (pred_var + gold_var + (pred_mean - gold_mean)**2)
    return 1 - torch.mean(ccc_val)

def mse_loss(pred, gold):
    """Mean Squared Error loss"""
    return nn.MSELoss()(pred, gold)

class LabeledEEGDataset(Dataset):
    """
    Dataset class for labeled EEG data organized by subjects
    """
    def __init__(self, subject_dirs, window_size=5, overlap=0.5, fs=256):
        """
        Args:
            subject_dirs: List of subject directory paths
            window_size: Window size in seconds for segmentation
            overlap: Overlap ratio between windows (0-1)
            fs: Sampling frequency
        """
        self.subject_dirs = subject_dirs
        self.window_size = window_size
        self.overlap = overlap
        self.fs = fs
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
        
        return (
            torch.FloatTensor(spec),      # Shape: (3, 224, 224)
            torch.FloatTensor(de),        # Shape: (26,)
            torch.FloatTensor(label)      # Shape: (2,) [valence, arousal]
        )

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
    
    # Create data loader
    dataloader = DataLoader(
        dataset, 
        batch_size=args.batch_size, 
        shuffle=True,
        num_workers=0  # Avoid multiprocessing issues
    )
    
    # Initialize model
    model = EmotionNet().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=5
    )
    
    # Training loop
    print(f"Starting training for {args.epochs} epochs...")
    print(f"Batch size: {args.batch_size}, Learning rate: {args.lr}")
    print(f"Window size: {args.window_size}s, Overlap: {args.overlap}")
    
    best_loss = float('inf')
    patience_counter = 0
    
    for epoch in range(args.epochs):
        model.train()
        total_loss = 0.0
        
        for batch_idx, (spec, de, labels) in enumerate(dataloader):
            spec = spec.to(device)
            de = de.to(device)
            labels = labels.to(device)
            
            optimizer.zero_grad()
            pred = model(spec, de)
            
            # Use MSE loss for continuous labels
            loss = mse_loss(pred, labels)
            
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            
            total_loss += loss.item()
            
            if batch_idx % 10 == 0:
                print(f"E{epoch+1}/{args.epochs} Batch {batch_idx}/{len(dataloader)} loss={loss.item():.4f}")
        
        avg_loss = total_loss / len(dataloader)
        print(f"E{epoch+1}/{args.epochs} loss={avg_loss:.4f}")
        
        # Save best model
        if avg_loss < best_loss:
            best_loss = avg_loss
            patience_counter = 0
            torch.save(model.state_dict(), args.checkpoint_path)
            print(f"New best model saved! Loss: {best_loss:.4f}")
        else:
            patience_counter += 1
        
        # Learning rate scheduling
        scheduler.step(avg_loss)
        
        # Early stopping
        if patience_counter >= 10:
            print(f"Early stopping triggered at epoch {epoch+1}")
            break
    
    print(f"Training completed. Best loss: {best_loss:.4f}")
    
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
    parser.add_argument('--checkpoint_path', type=str, default='model_training/ckpt.pt',
                        help='Path to save the best model checkpoint')
    parser.add_argument('--onnx_path', type=str, default='model/va_regressor.onnx',
                        help='Path to export ONNX model')
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    train(args)