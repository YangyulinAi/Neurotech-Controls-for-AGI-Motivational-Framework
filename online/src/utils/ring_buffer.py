# online/src/utils/ring_buffer.py
import threading
import numpy as np

class RingBuffer:
    def __init__(self, size, n_channels):
        self.size = size
        self.n_channels = n_channels
        self.buffer = np.zeros((size, n_channels), dtype=np.float32)
        self.index = 0
        self.lock = threading.Lock()

    def extend(self, data):
        with self.lock:
            n = data.shape[0]
            if n >= self.size:
                self.buffer = data[-self.size:]
                self.index = 0
            else:
                end = (self.index + n) % self.size
                if end > self.index:
                    self.buffer[self.index:end] = data
                else:
                    part1 = self.size - self.index
                    self.buffer[self.index:] = data[:part1]
                    self.buffer[:end] = data[part1:]
                self.index = end

    def get(self, length):
        with self.lock:
            if length > self.size:
                raise ValueError("Request length exceeds buffer size")
            end = self.index
            start = (end - length) % self.size
            if start < end:
                return self.buffer[start:end].copy()
            else:
                return np.vstack((self.buffer[start:], self.buffer[:end]))