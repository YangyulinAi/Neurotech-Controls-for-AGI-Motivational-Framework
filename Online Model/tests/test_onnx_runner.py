# online/tests/test_onnx_runner.py
import numpy as np
from src.onnx_runner import ONNXRunner

def test_onnx_output_shape(tmp_path):
    # create dummy ONNX or assume real model
    model_path = 'models/va_regressor.onnx'
    runner = ONNXRunner(model_path)
    data = np.random.randn(1, 8, 256).astype(np.float32)
    out = runner.predict(data)
    assert out.shape == (1, 2)