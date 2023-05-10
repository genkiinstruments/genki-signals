import numpy as np

from genki_signals.signal_sources.base import SignalSource


class RandomNoise(SignalSource):
    def __init__(self, amplitude=1):
        self.amplitude = amplitude

    def __call__(self):
        return self.amplitude * np.random.randn()

    def __repr__(self):
        return f"RandomNoise(amplitude={self.amplitude})"
