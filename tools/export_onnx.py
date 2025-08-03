#!/usr/bin/env python3
"""
ONNX Export Tool for Neural Axis BCI Models
Converts PyTorch trained models to ONNX format for production deployment
"""

import argparse
import sys
import torch
import onnx
import onnxruntime as ort
import numpy as np
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from train.model_cnn_tcn import EmotionNet


def export_to_onnx(weights_path, output_path, model_type='CNN', batch_size=1, 
                   use_batch_norm=False, dropout_rate=0.0, validate=True):
    """
    Export PyTorch model to ONNX format
    
    Args:
        weights_path: Path to PyTorch model weights (.pth file)
        output_path: Path to save ONNX model
        model_type: Model architecture type
        batch_size: Batch size for model (use 1 for dynamic)
        use_batch_norm: Whether model uses batch normalization
        dropout_rate: Dropout rate used in model
        validate: Whether to validate the exported model
    """
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # Initialize model
    if model_type == 'CNN':
        model = EmotionNet(use_batch_norm=use_batch_norm, dropout_rate=dropout_rate)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
    
    # Load weights
    print(f"Loading model weights from: {weights_path}")
    if not Path(weights_path).exists():
        raise FileNotFoundError(f"Model weights not found: {weights_path}")
    
    state_dict = torch.load(weights_path, map_location=device)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    
    print("Model loaded successfully")
    
    # Create dummy inputs for tracing
    dummy_spec = torch.randn(batch_size, 3, 224, 224).to(device)
    dummy_de = torch.randn(batch_size, 26).to(device)
    
    print("Creating dummy inputs for ONNX export...")
    print(f"  Spectrogram shape: {dummy_spec.shape}")
    print(f"  Differential Entropy shape: {dummy_de.shape}")
    
    # Test model with dummy inputs
    try:
        with torch.no_grad():
            test_output = model(dummy_spec, dummy_de)
            print(f"  Model output shape: {test_output.shape}")
    except Exception as e:
        raise RuntimeError(f"Model forward pass failed: {e}")
    
    # Export to ONNX
    print(f"Exporting to ONNX: {output_path}")
    
    # Create output directory if it doesn't exist
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        torch.onnx.export(
            model,
            (dummy_spec, dummy_de),
            output_path,
            export_params=True,
            opset_version=11,
            do_constant_folding=True,
            input_names=['spec', 'de'],
            output_names=['valence_arousal'],
            dynamic_axes={
                'spec': {0: 'batch_size'},
                'de': {0: 'batch_size'},
                'valence_arousal': {0: 'batch_size'}
            } if batch_size == 1 else None,
            verbose=False
        )
        print("✓ ONNX export completed successfully")
        
    except Exception as e:
        raise RuntimeError(f"ONNX export failed: {e}")
    
    # Validate exported model
    if validate:
        print("Validating exported ONNX model...")
        validate_onnx_model(output_path, dummy_spec, dummy_de, test_output.cpu().numpy())
    
    # Print model information
    print_model_info(output_path)
    
    return output_path


def validate_onnx_model(onnx_path, dummy_spec, dummy_de, expected_output):
    """
    Validate the exported ONNX model by comparing outputs
    """
    try:
        # Load ONNX model
        onnx_model = onnx.load(onnx_path)
        onnx.checker.check_model(onnx_model)
        print("✓ ONNX model structure is valid")
        
        # Test with ONNX Runtime
        session = ort.InferenceSession(onnx_path, providers=['CPUExecutionProvider'])
        
        # Prepare inputs
        inputs = {
            'spec': dummy_spec.cpu().numpy().astype(np.float32),
            'de': dummy_de.cpu().numpy().astype(np.float32)
        }
        
        # Run inference
        outputs = session.run(['valence_arousal'], inputs)
        onnx_output = outputs[0]
        
        # Compare outputs
        diff = np.abs(expected_output - onnx_output).max()
        if diff < 1e-5:
            print(f"✓ ONNX validation passed (max diff: {diff:.2e})")
        else:
            print(f"⚠ ONNX validation warning: max difference {diff:.2e}")
            
    except Exception as e:
        print(f"❌ ONNX validation failed: {e}")


def print_model_info(onnx_path):
    """Print information about the exported ONNX model"""
    try:
        model = onnx.load(onnx_path)
        
        print("\n" + "="*50)
        print("ONNX MODEL INFORMATION")
        print("="*50)
        
        # Model size
        file_size = Path(onnx_path).stat().st_size
        print(f"File size: {file_size / (1024*1024):.2f} MB")
        
        # Inputs
        print("Inputs:")
        for input_info in model.graph.input:
            shape = [dim.dim_value for dim in input_info.type.tensor_type.shape.dim]
            print(f"  - {input_info.name}: {shape}")
        
        # Outputs
        print("Outputs:")
        for output_info in model.graph.output:
            shape = [dim.dim_value for dim in output_info.type.tensor_type.shape.dim]
            print(f"  - {output_info.name}: {shape}")
        
        # Operators
        op_types = set(node.op_type for node in model.graph.node)
        print(f"Operators used: {len(op_types)}")
        print(f"  {', '.join(sorted(op_types))}")
        
        print("="*50)
        
    except Exception as e:
        print(f"Could not analyze model info: {e}")


def main():
    parser = argparse.ArgumentParser(description='Export PyTorch model to ONNX format')
    parser.add_argument('--weights', required=True, help='Path to PyTorch weights file (.pth)')
    parser.add_argument('--output', help='Output ONNX file path (default: auto-generated)')
    parser.add_argument('--model_type', default='CNN', choices=['CNN'], help='Model architecture type')
    parser.add_argument('--batch_size', type=int, default=1, help='Batch size (1 for dynamic)')
    parser.add_argument('--use_batch_norm', action='store_true', help='Model uses batch normalization')
    parser.add_argument('--dropout_rate', type=float, default=0.0, help='Dropout rate used in model')
    parser.add_argument('--no_validate', action='store_true', help='Skip model validation')
    
    args = parser.parse_args()
    
    # Auto-generate output path if not provided
    if not args.output:
        weights_path = Path(args.weights)
        args.output = weights_path.parent / f"{weights_path.stem}.onnx"
    
    try:
        export_to_onnx(
            weights_path=args.weights,
            output_path=args.output,
            model_type=args.model_type,
            batch_size=args.batch_size,
            use_batch_norm=args.use_batch_norm,
            dropout_rate=args.dropout_rate,
            validate=not args.no_validate
        )
        
        print(f"\n🎉 Export completed successfully!")
        print(f"ONNX model saved to: {args.output}")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()