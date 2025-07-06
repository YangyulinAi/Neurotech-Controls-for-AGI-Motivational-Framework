# online/tests/test_preprocess.py
import numpy as np
from src.preprocess import Preprocessor

def test_preprocess_shape():
    data = np.random.randn(256, 8)
    pre = Preprocessor(256, 1, 45)
    out = pre.transform(data)
    assert out.shape == data.shape
    assert np.allclose(np.mean(out,0), 0, atol=1e-6)