import argparse, os, torch, torch.optim as optim
from torch.utils.data import DataLoader
from dataset import EEGWindowSet
from model_cnn_tcn import EmotionNet

def ccc(pred, gold):
    vx = pred - pred.mean(0)
    vy = gold - gold.mean(0)
    rho = (vx * vy).mean() / torch.sqrt(vx.var()*vy.var() + 1e-8)
    return 1 - rho

def train(args):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    ds = EEGWindowSet(args.data)
    dl = DataLoader(ds, batch_size=32, shuffle=True, num_workers=4)
    net = EmotionNet().to(device)
    opt = optim.Adam(net.parameters(), lr=1e-3)
    os.makedirs(args.out, exist_ok=True)
    best = float('inf')

    for e in range(1, args.epochs+1):
        tot = 0
        for spec,de,y in dl:
            spec,de,y = spec.to(device),de.to(device),y.to(device)
            pred = net(spec,de)
            loss = ccc(pred,y)
            opt.zero_grad(); loss.backward(); opt.step()
            tot += loss.item() * y.size(0)
        avg = tot / len(ds)
        print(f"E{e}/{args.epochs} loss={avg:.4f}")
        if avg < best:
            best = avg
            torch.save(net.state_dict(), os.path.join(args.out,'ckpt.pt'))
    print(f"Done. Best={best:.4f}")

if __name__=='__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--data',   required=True)
    p.add_argument('--out',    default='ckpt')
    p.add_argument('--epochs', type=int, default=30)
    args = p.parse_args()
    train(args)
