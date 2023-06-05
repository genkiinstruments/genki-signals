import numpy as np
from scipy import signal

from genki_signals.functions.base import SignalFunction, SignalName


class SineWave(SignalFunction):
    """
    Generate a sine wave from an input signal (usually time)
    """

    def __init__(self, input_signal: SignalName, name: str, amplitude: float, frequency: float, phase: float):
        super().__init__(
            input_signal, name=name, params={"amplitude": amplitude, "frequency": frequency, "phase": phase}
        )
        self.amplitude = amplitude
        self.frequency = frequency
        self.phase = phase

    def __call__(self, input_signal):
        return self.amplitude * np.sin(2 * np.pi * self.frequency * input_signal + self.phase)


class SquareWave(SignalFunction):
    """
    Generate a square wave from an input signal (usually time)
    """

    def __init__(self, input_signal: SignalName, name: str, amplitude: float, frequency: float, phase: float):
        super().__init__(
            input_signal, name=name, params={"amplitude": amplitude, "frequency": frequency, "phase": phase}
        )
        self.amplitude = amplitude
        self.frequency = frequency
        self.phase = phase

    def __call__(self, input_signal):
        return self.amplitude * signal.square(2 * np.pi * self.frequency * input_signal + self.phase)


class TriangleWave(SignalFunction):
    """
    Generate a triangular wave from an input signal (usually time)
    """

    def __init__(self, input_signal: SignalName, name: str, amplitude: float, frequency: float, phase: float):
        super().__init__(
            input_signal, name=name, params={"amplitude": amplitude, "frequency": frequency, "phase": phase}
        )
        self.amplitude = amplitude
        self.frequency = frequency
        self.phase = phase

    def __call__(self, input_signal):
        return self.amplitude * signal.sawtooth(2 * np.pi * self.frequency * input_signal + self.phase, 0.5)


__all__ = [
    "SineWave",
    "SquareWave",
    "TriangleWave",
]
