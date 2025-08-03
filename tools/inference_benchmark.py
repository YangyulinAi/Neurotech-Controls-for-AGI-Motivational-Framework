#!/usr/bin/env python3
"""
ONNX Inference Benchmark Tool
Tests model performance across different execution providers
DFR5 Performance Optimization Tool
"""

import argparse
import time
import numpy as np
import onnxruntime as ort
from pathlib import Path
import json
import logging
from statistics import mean, median, stdev
from typing import List, Dict, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InferenceBenchmark:
    """
    Comprehensive benchmark for ONNX model inference performance
    """
    
    def __init__(self, model_path: str):
        """
        Initialize benchmark with model path
        
        Args:
            model_path: Path to ONNX model file
        """
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        self.results = {}
        logger.info(f"Initialized benchmark for: {self.model_path}")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available execution providers"""
        available = ort.get_available_providers()
        logger.info(f"Available providers: {available}")
        return available
    
    def create_sample_inputs(self, session) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sample inputs matching model requirements
        
        Args:
            session: ONNX runtime session
            
        Returns:
            Tuple of sample inputs (spec, de)
        """
        inputs = session.get_inputs()
        
        # Assume standard BCI model inputs: spectrogram and DE features
        if len(inputs) >= 2:
            # First input: spectrogram (1, 3, 224, 224)
            spec_shape = inputs[0].shape
            spec_shape = [1 if dim is None else dim for dim in spec_shape]
            if len(spec_shape) == 4 and spec_shape[1] == 3:
                spec_input = np.random.randn(*spec_shape).astype(np.float32)
            else:
                spec_input = np.random.randn(1, 3, 224, 224).astype(np.float32)
            
            # Second input: DE features (1, 26)
            de_shape = inputs[1].shape
            de_shape = [1 if dim is None else dim for dim in de_shape]
            if len(de_shape) == 2 and de_shape[1] in [26, 30, 20]:
                de_input = np.random.randn(*de_shape).astype(np.float32)
            else:
                de_input = np.random.randn(1, 26).astype(np.float32)
        else:
            # Default shapes for BCI emotion recognition
            spec_input = np.random.randn(1, 3, 224, 224).astype(np.float32)
            de_input = np.random.randn(1, 26).astype(np.float32)
        
        logger.info(f"Created sample inputs - Spec: {spec_input.shape}, DE: {de_input.shape}")
        return spec_input, de_input
    
    def benchmark_provider(self, provider: str, num_iterations: int = 100, 
                          warmup_iterations: int = 10) -> Dict:
        """
        Benchmark specific execution provider
        
        Args:
            provider: Execution provider name
            num_iterations: Number of inference iterations
            warmup_iterations: Number of warmup iterations
            
        Returns:
            Benchmark results dictionary
        """
        logger.info(f"Benchmarking provider: {provider}")
        
        try:
            # Create session with specific provider
            session = ort.InferenceSession(str(self.model_path), providers=[provider])
            
            # Create sample inputs
            spec_input, de_input = self.create_sample_inputs(session)
            
            # Get input and output names
            input_names = [inp.name for inp in session.get_inputs()]
            output_names = [out.name for out in session.get_outputs()]
            
            # Prepare feed dictionary
            if len(input_names) >= 2:
                feed_dict = {
                    input_names[0]: spec_input,
                    input_names[1]: de_input
                }
            else:
                feed_dict = {input_names[0]: spec_input}
            
            # Warmup
            logger.info(f"Running {warmup_iterations} warmup iterations...")
            for _ in range(warmup_iterations):
                _ = session.run(output_names, feed_dict)
            
            # Benchmark
            logger.info(f"Running {num_iterations} benchmark iterations...")
            inference_times = []
            
            for i in range(num_iterations):
                start_time = time.perf_counter()
                outputs = session.run(output_names, feed_dict)
                end_time = time.perf_counter()
                
                inference_time = (end_time - start_time) * 1000  # Convert to milliseconds
                inference_times.append(inference_time)
                
                if (i + 1) % 20 == 0:
                    logger.info(f"Completed {i + 1}/{num_iterations} iterations")
            
            # Calculate statistics
            avg_time = mean(inference_times)
            median_time = median(inference_times)
            std_time = stdev(inference_times) if len(inference_times) > 1 else 0.0
            min_time = min(inference_times)
            max_time = max(inference_times)
            throughput = 1000.0 / avg_time  # Inferences per second
            
            # Validate output
            sample_output = outputs[0] if outputs else None
            output_shape = sample_output.shape if sample_output is not None else "Unknown"
            
            results = {
                'provider': provider,
                'status': 'success',
                'num_iterations': num_iterations,
                'average_time_ms': avg_time,
                'median_time_ms': median_time,
                'std_time_ms': std_time,
                'min_time_ms': min_time,
                'max_time_ms': max_time,
                'throughput_fps': throughput,
                'output_shape': str(output_shape),
                'all_times': inference_times
            }
            
            logger.info(f"✓ {provider} - Avg: {avg_time:.2f}ms, Throughput: {throughput:.1f} FPS")
            return results
            
        except Exception as e:
            logger.error(f"✗ {provider} failed: {e}")
            return {
                'provider': provider,
                'status': 'failed',
                'error': str(e)
            }
    
    def run_comprehensive_benchmark(self, num_iterations: int = 100) -> Dict:
        """
        Run benchmark across all available providers
        
        Args:
            num_iterations: Number of iterations per provider
            
        Returns:
            Complete benchmark results
        """
        logger.info("Starting comprehensive benchmark...")
        
        available_providers = self.get_available_providers()
        benchmark_results = {
            'model_path': str(self.model_path),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'num_iterations': num_iterations,
            'providers': []
        }
        
        for provider in available_providers:
            result = self.benchmark_provider(provider, num_iterations)
            benchmark_results['providers'].append(result)
        
        # Find best provider
        successful_results = [r for r in benchmark_results['providers'] if r['status'] == 'success']
        if successful_results:
            best_provider = min(successful_results, key=lambda x: x['average_time_ms'])
            benchmark_results['best_provider'] = best_provider['provider']
            benchmark_results['best_time_ms'] = best_provider['average_time_ms']
            benchmark_results['best_throughput_fps'] = best_provider['throughput_fps']
        
        self.results = benchmark_results
        return benchmark_results
    
    def save_results(self, output_file: str = None):
        """
        Save benchmark results to JSON file
        
        Args:
            output_file: Output file path (auto-generated if None)
        """
        if not self.results:
            logger.warning("No results to save. Run benchmark first.")
            return
        
        if output_file is None:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            model_name = self.model_path.stem
            output_file = f"benchmark_{model_name}_{timestamp}.json"
        
        # Remove detailed timing data for cleaner output
        clean_results = self.results.copy()
        for provider_result in clean_results['providers']:
            if 'all_times' in provider_result:
                del provider_result['all_times']
        
        with open(output_file, 'w') as f:
            json.dump(clean_results, f, indent=2)
        
        logger.info(f"Results saved to: {output_file}")
    
    def print_summary(self):
        """Print benchmark summary to console"""
        if not self.results:
            logger.warning("No results to display. Run benchmark first.")
            return
        
        print("\n" + "="*60)
        print("ONNX INFERENCE BENCHMARK SUMMARY")
        print("="*60)
        print(f"Model: {self.results['model_path']}")
        print(f"Iterations: {self.results['num_iterations']}")
        print(f"Timestamp: {self.results['timestamp']}")
        
        if 'best_provider' in self.results:
            print(f"\n🏆 Best Provider: {self.results['best_provider']}")
            print(f"   Average Time: {self.results['best_time_ms']:.2f} ms")
            print(f"   Throughput: {self.results['best_throughput_fps']:.1f} FPS")
        
        print(f"\n{'Provider':<20} {'Status':<10} {'Avg Time (ms)':<15} {'Throughput (FPS)':<18}")
        print("-" * 70)
        
        for result in self.results['providers']:
            provider = result['provider']
            status = result['status']
            
            if status == 'success':
                avg_time = f"{result['average_time_ms']:.2f}"
                throughput = f"{result['throughput_fps']:.1f}"
            else:
                avg_time = "N/A"
                throughput = "N/A"
            
            print(f"{provider:<20} {status:<10} {avg_time:<15} {throughput:<18}")
        
        print("="*60)


def main():
    """Main function for command-line interface"""
    parser = argparse.ArgumentParser(description="ONNX Model Inference Benchmark")
    parser.add_argument('model_path', help='Path to ONNX model file')
    parser.add_argument('--iterations', '-i', type=int, default=100,
                       help='Number of inference iterations (default: 100)')
    parser.add_argument('--output', '-o', type=str, default=None,
                       help='Output file for results (auto-generated if not specified)')
    parser.add_argument('--providers', '-p', nargs='+', default=None,
                       help='Specific providers to test (default: all available)')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Reduce console output')
    
    args = parser.parse_args()
    
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    try:
        # Initialize benchmark
        benchmark = InferenceBenchmark(args.model_path)
        
        # Run benchmark
        if args.providers:
            # Test specific providers
            results = {
                'model_path': args.model_path,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'num_iterations': args.iterations,
                'providers': []
            }
            
            for provider in args.providers:
                result = benchmark.benchmark_provider(provider, args.iterations)
                results['providers'].append(result)
            
            benchmark.results = results
        else:
            # Test all providers
            benchmark.run_comprehensive_benchmark(args.iterations)
        
        # Display and save results
        benchmark.print_summary()
        benchmark.save_results(args.output)
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())