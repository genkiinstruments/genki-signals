import numpy as np
from scipy import signal

from genki_signals.data_sources.base import DataSource


class SineWave(DataSource):
    def __init__(self, amplitude, frequency, phase):
        self.amplitude = amplitude
        self.frequency = frequency
        self.phase = phase

    def __call__(self, t):
        return self.amplitude * np.sin(2 * np.pi * self.frequency * t + self.phase)

    def __repr__(self):
        return f"SineWave(amplitude={self.amplitude}, frequency={self.frequency}, phase={self.phase})"


class SquareWave(DataSource):
    def __init__(self, amplitude, frequency, phase):
        self.amplitude = amplitude
        self.frequency = frequency
        self.phase = phase

    def __call__(self, t):
        return self.amplitude * signal.square(
            2 * np.pi * self.frequency * t + self.phase
        )

    def __repr__(self):
        return f"SquareWave(amplitude={self.amplitude}, frequency={self.frequency}, phase={self.phase})"


class TriangleWave(DataSource):
    def __init__(self, amplitude, frequency, phase):
        self.amplitude = amplitude
        self.frequency = frequency
        self.phase = phase

    def __call__(self, t):
        return self.amplitude * signal.sawtooth(
            2 * np.pi * self.frequency * t + self.phase, 0.5
        )

    def __repr__(self):
        return f"TriangleWave(amplitude={self.amplitude}, frequency={self.frequency}, phase={self.phase})"


class RandomNoise(DataSource):
    def __init__(self, amplitude=1):
        self.amplitude = amplitude

    def __call__(self, t):
        return self.amplitude * np.random.randn()

    def __repr__(self):
        return f"RandomNoise(amplitude={self.amplitude})"
