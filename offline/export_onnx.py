import argparse, sys, torch
import torch.nn.utils.prune as prune
from model_cnn_tcn import EmotionNet

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--ckpt', default='ckpt/ckpt.pt')
    p.add_argument('--out',  default='emotion_va.onnx')
    return p.parse_args()

if __name__=='__main__':
    args = parse_args()
    try:
        import onnx
    except ModuleNotFoundError:
        print("Please install onnx: pip install onnx", file=sys.stderr)
        sys.exit(1)

    model = EmotionNet()
    model.load_state_dict(torch.load(args.ckpt, map_location='cpu'))
    model.eval()

    for m in model.modules():
        if isinstance(m, (torch.nn.Conv2d, torch.nn.Linear)):
            prune.l1_unstructured(m, 'weight', amount=0.1)
            prune.remove(m, 'weight')

    dummy_spec = torch.randn(1,3,224,224)
    dummy_de   = torch.randn(1,26)
    torch.onnx.export(
        model, (dummy_spec, dummy_de), args.out,
        input_names=['spec','de'], output_names=['va'],
        opset_version=12, do_constant_folding=True
    )
    print(f"ONNX exported to {args.out}")
