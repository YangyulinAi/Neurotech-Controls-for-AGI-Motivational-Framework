# online/src/onnx_runner.py
import onnxruntime as ort
import numpy as np

class ONNXRunner:
    def __init__(self, model_path):
        """
        Initialize ONNX Runtime session with CPU provider.
        Automatically discover all model inputs
        """
        # Create inference session using CPU provider
        self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        # Collect all input names, preserving the order defined in the ONNX model
        inputs = self.session.get_inputs()
        self.input_names = [inp.name for inp in inputs]

        self.output_name = self.session.get_outputs()[0].name

    def predict(self, spec: np.ndarray, de: np.ndarray) -> np.ndarray:
        """
        Run inference on the model given spectrogram and differential entropy.

        Args:
            spec: np.ndarray with shape (1, 3, 224, 224)
            de:   np.ndarray with shape (1, 26)

        Returns:
            np.ndarray with shape (1, 2), representing [valence, arousal].
        """
        # Prepare the input feed dictionary for both model inputs
        feed = {
            self.input_names[0]: spec.astype(np.float32),
            self.input_names[1]: de.astype(np.float32),
        }
        # Execute the model
        outputs = self.session.run([self.output_name], feed)
        return np.array(outputs[0])  # shape: (1, 2)