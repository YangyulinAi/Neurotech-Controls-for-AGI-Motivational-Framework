import argparse, os, torch, torch.optim as optim
import numpy as np
from torch.utils.data import DataLoader
from dataset_set import EEGSetDataset
from model_cnn_tcn import EmotionNet

def ccc(pred, gold):
    """Concordance Correlation Coefficient loss"""
    vx = pred - pred.mean(0)
    vy = gold - gold.mean(0)
    rho = (vx * vy).mean() / torch.sqrt(vx.var()*vy.var() + 1e-8)
    return 1 - rho

def mse_loss(pred, gold):
    """Mean Squared Error loss"""
    return torch.nn.functional.mse_loss(pred, gold)

def train(args):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # Create dataset with larger windows for better features
    ds = EEGSetDataset(
        args.data, 
        window_size=args.window_size,
        overlap=args.overlap,
        fs=args.fs
    )
    
    print(f"Dataset size: {len(ds)} windows")
    
    if len(ds) == 0:
        print("No data found! Check the data directory.")
        return
    
    # Data loader with optimized parameters
    dl = DataLoader(
        ds, 
        batch_size=args.batch_size, 
        shuffle=True, 
        num_workers=args.num_workers,
        pin_memory=True if device.type == 'cuda' else False
    )
    
    # Model and optimizer
    net = EmotionNet().to(device)
    
    # Optimizer with learning rate scheduling
    if args.optimizer == 'adam':
        opt = optim.Adam(net.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    elif args.optimizer == 'sgd':
        opt = optim.SGD(net.parameters(), lr=args.lr, momentum=0.9, weight_decay=args.weight_decay)
    else:
        opt = optim.AdamW(net.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    
    # Learning rate scheduler
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        opt, mode='min', factor=0.5, patience=10
    )
    
    # Loss function
    if args.loss == 'ccc':
        criterion = ccc
    else:
        criterion = mse_loss
    
    os.makedirs(args.out, exist_ok=True)
    best = float('inf')
    patience_counter = 0
    
    print(f"Starting training for {args.epochs} epochs...")
    print(f"Batch size: {args.batch_size}, Learning rate: {args.lr}")
    print(f"Window size: {args.window_size}s, Overlap: {args.overlap}")
    
    for e in range(1, args.epochs+1):
        net.train()
        tot_loss = 0
        num_batches = 0
        
        for batch_idx, (spec, de, y) in enumerate(dl):
            spec, de, y = spec.to(device), de.to(device), y.to(device)
            
            opt.zero_grad()
            pred = net(spec, de)
            loss = criterion(pred, y)
            loss.backward()
            
            # Gradient clipping to prevent exploding gradients
            torch.nn.utils.clip_grad_norm_(net.parameters(), max_norm=1.0)
            
            opt.step()
            
            tot_loss += loss.item()
            num_batches += 1
            
            # Print progress every 10 batches
            if batch_idx % 10 == 0:
                current_loss = loss.item()
                print(f"E{e}/{args.epochs} Batch {batch_idx}/{len(dl)} loss={current_loss:.4f}")
        
        avg_loss = tot_loss / num_batches
        print(f"E{e}/{args.epochs} loss={avg_loss:.4f}")
        
        # Learning rate scheduling
        scheduler.step(avg_loss)
        
        # Save best model
        if avg_loss < best:
            best = avg_loss
            torch.save(net.state_dict(), os.path.join(args.out, 'ckpt.pt'))
            patience_counter = 0
            print(f"New best model saved! Loss: {best:.4f}")
        else:
            patience_counter += 1
        
        # Early stopping
        if args.early_stopping > 0 and patience_counter >= args.early_stopping:
            print(f"Early stopping triggered after {patience_counter} epochs without improvement")
            break
    
    print(f"Training completed. Best loss: {best:.4f}")

if __name__=='__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--data', required=True, help='Path to directory containing .set files')
    p.add_argument('--out', default='ckpt', help='Output directory for model checkpoint')
    p.add_argument('--epochs', type=int, default=50, help='Number of training epochs')
    p.add_argument('--batch_size', type=int, default=16, help='Batch size')
    p.add_argument('--lr', type=float, default=1e-4, help='Learning rate')
    p.add_argument('--weight_decay', type=float, default=1e-5, help='Weight decay for regularization')
    p.add_argument('--optimizer', choices=['adam', 'sgd', 'adamw'], default='adamw', help='Optimizer type')
    p.add_argument('--loss', choices=['ccc', 'mse'], default='ccc', help='Loss function')
    p.add_argument('--window_size', type=float, default=5.0, help='Window size in seconds')
    p.add_argument('--overlap', type=float, default=0.5, help='Overlap ratio between windows')
    p.add_argument('--fs', type=int, default=256, help='Sampling frequency')
    p.add_argument('--num_workers', type=int, default=2, help='Number of data loader workers')
    p.add_argument('--early_stopping', type=int, default=20, help='Early stopping patience (0 to disable)')
    
    args = p.parse_args()
    
    # Validate arguments
    if not os.path.exists(args.data):
        print(f"Error: Data directory {args.data} does not exist")
        exit(1)
    
    if args.overlap < 0 or args.overlap >= 1:
        print("Error: Overlap must be between 0 and 1")
        exit(1)
    
    train(args)