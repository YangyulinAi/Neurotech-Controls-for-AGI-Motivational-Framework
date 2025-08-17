"""
Enhanced ONNX Runtime with automatic GPU/CPU fallback and provider optimization
"""
import onnxruntime as ort
import numpy as np
from typing import Tuple, List, Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)

class ONNXRunner:
    """Enhanced ONNX inference with GPU/CPU dual provider support"""
    
    def __init__(self, model_path: str, use_gpu: bool = True):
        """
        Initialize ONNX Runtime with automatic provider fallback
        
        Args:
            model_path: Path to ONNX model file
            use_gpu: Whether to attempt GPU acceleration (falls back to CPU)
        """
        self.model_path = model_path
        
        # Configure providers with GPU/CPU fallback
        providers = []
        if use_gpu:
            # Try CUDA first for NVIDIA GPUs
            if "CUDAExecutionProvider" in ort.get_available_providers():
                providers.append("CUDAExecutionProvider")
                logger.info("CUDA provider available - enabling GPU acceleration")
            else:
                logger.info("CUDA provider not available - using CPU only")
        
        # Always include CPU as fallback
        providers.append("CPUExecutionProvider")
        
        # Optimize session options for performance
        session_options = ort.SessionOptions()
        session_options.intra_op_num_threads = 1  # Prevent oversubscription
        session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        try:
            # Create inference session with optimized providers
            self.session = ort.InferenceSession(
                model_path, 
                sess_options=session_options, 
                providers=providers
            )
            
            # Log active providers
            active_providers = self.session.get_providers()
            logger.info(f"ONNX session initialized with providers: {active_providers}")
            
            # Cache input/output metadata for efficiency
            self.input_names = [inp.name for inp in self.session.get_inputs()]
            self.output_names = [out.name for out in self.session.get_outputs()]
            
            logger.info(f"Model loaded: {len(self.input_names)} inputs, {len(self.output_names)} outputs")
            
        except Exception as e:
            logger.error(f"Failed to initialize ONNX session: {e}")
            raise RuntimeError(f"ONNX model loading failed: {e}")
    
    def predict(self, spectrograms: np.ndarray, differential_entropy: np.ndarray) -> Tuple[float, float]:
        """
        Run emotion prediction inference
        
        Args:
            spectrograms: Spectrogram features (batch_size, 3, 224, 224)
            differential_entropy: DE features (batch_size, num_features)
            
        Returns:
            Tuple of (valence, arousal) values
        """
        try:
            # Ensure inputs are float32 for ONNX compatibility
            spec_input = spectrograms.astype(np.float32)
            de_input = differential_entropy.astype(np.float32)
            
            # Prepare input dictionary
            inputs = {
                self.input_names[0]: spec_input,
                self.input_names[1]: de_input
            }
            
            # Run inference
            outputs = self.session.run(self.output_names, inputs)
            
            # Extract valence and arousal (assuming 2D output: [valence, arousal])
            if len(outputs) == 1:
                # Single output with both values
                valence, arousal = outputs[0][0]
            else:
                # Separate outputs
                valence = float(outputs[0][0])
                arousal = float(outputs[1][0])
            
            return float(valence), float(arousal)
            
        except Exception as e:
            logger.error(f"ONNX inference failed: {e}")
            logger.error(f"Input shapes - Spec: {spectrograms.shape}, DE: {differential_entropy.shape}")
            raise RuntimeError(f"Inference failed: {e}")
    
    def get_provider_info(self) -> dict:
        """Get information about active providers"""
        return {
            "providers": self.session.get_providers(),
            "input_names": self.input_names,
            "output_names": self.output_names,
            "model_path": self.model_path
        }
    
    def benchmark(self, num_iterations: int = 10) -> dict:
        """
        Simple benchmark for performance testing
        
        Args:
            num_iterations: Number of inference iterations to run
            
        Returns:
            Benchmark results dictionary
        """
        import time
        
        # Create dummy inputs matching expected shapes
        dummy_spec = np.random.randn(1, 3, 224, 224).astype(np.float32)
        dummy_de = np.random.randn(1, 26).astype(np.float32)  # Assuming 26 DE features
        
        # Warmup
        self.predict(dummy_spec, dummy_de)
        
        # Benchmark
        times = []
        for _ in range(num_iterations):
            start = time.time()
            self.predict(dummy_spec, dummy_de)
            times.append(time.time() - start)
        
        return {
            "iterations": num_iterations,
            "mean_time_ms": np.mean(times) * 1000,
            "std_time_ms": np.std(times) * 1000,
            "min_time_ms": np.min(times) * 1000,
            "max_time_ms": np.max(times) * 1000,
            "providers": self.session.get_providers()
        }


# Backward compatibility alias
class ONNXModel(ONNXRunner):
    """Legacy alias for ONNXRunner - maintains backward compatibility"""
    pass