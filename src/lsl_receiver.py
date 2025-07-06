# online/src/lsl_receiver.py
from pylsl import StreamInlet, resolve_stream
from .utils.ring_buffer import RingBuffer
import logging
import numpy as np
class LSLReceiver:
    def __init__(self, sampling_rate, window_size, n_channels, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.buf_samples = int(sampling_rate * window_size * 2)
        self.ring = RingBuffer(self.buf_samples, n_channels)
        streams = resolve_stream('type', 'EEG')
        self.inlet = StreamInlet(streams[0])
        self.logger.info(f"Connected to LSL stream: {streams[0].name()}")

    def start(self):
        self.logger.info("Starting LSL receiver loop...")
        while True:
            sample, _ = self.inlet.pull_sample()
            self.ring.extend(np.array([sample]))