from __future__ import annotations

import numpy as np
from scipy import integrate

from genki_signals.buffers import NumpyBuffer
from genki_signals.signal_functions.base import SignalFunction, SignalName


class Scale(SignalFunction):
    """
    Scale an input signal by a constant factor
    """
    def __init__(self, input_signal: SignalName, scale_factor: float, name: str):
        super().__init__(input_signal, name=name, params={"scale_factor": scale_factor})
        self.scale_factor = scale_factor

    def __call__(self, x):
        return x * self.scale_factor


class Sum(SignalFunction):
    """Sum multiple signals"""
    def __call__(self, *inputs):
        return sum(inputs)


class Difference(SignalFunction):
    """Find the difference between 2 signals"""

    def __call__(self, a, b):
        return a - b


class Multiply(SignalFunction):
    """Multiply 2 signals"""
    def __init__(self, input_a: SignalName, input_b: SignalName, name: str):
        super().__init__(input_a, input_b, name=name)

    def __call__(self, a, b):
        return a * b


class Integrate(SignalFunction):
    """Integrates a signal with respect to another signal (usually time)"""

    def __init__(
        self,
        input_a: SignalName,
        input_b: SignalName,
        name: str,
        use_trapz: bool = True,
    ):
        super().__init__(input_a, input_b, name=name, params={"use_trapz": use_trapz})
        self.trapezoid = use_trapz
        self.state = 0.0
        self.last_b = None

    def __call__(self, a, b):
        if self.trapezoid:
            val = self.state + integrate.cumulative_trapezoid(y=a, x=b, initial=0.0, axis=-1)
        else:
            prepend_b = b[..., 0:1] if self.last_b is None else self.last_b
            db = np.diff(b, prepend=prepend_b)
            val = self.state + a.cumsum(axis=-1) * db

        if len(val) > 0:
            self.state = val[..., -1]
            self.last_b = b[..., -1:]

        return val


class Differentiate(SignalFunction):
    """
    Differentiates a signal with respect to another signal (usually time).
    If input_b is None, the discrete difference of input_a is used.
    """

    def __init__(self, input_a: SignalName, input_b: SignalName, name: str):
        input_signals = [input_a] if input_b is None else [input_a, input_b]
        super().__init__(*input_signals, name=name)
        self.last_a = None
        self.last_b = None

    def __call__(self, a, b=None):
        if b is None:  # I.e. use discrete difference
            b = np.arange(len(a))

        prepend_a = a[..., 0:1] if self.last_a is None else self.last_a
        prepend_b = b[..., 0:1] if self.last_b is None else self.last_b
        da = np.diff(a, prepend=prepend_a)
        db = np.diff(b, prepend=prepend_b)

        # when there is no change in b, the derivative (da/db) is set to 0
        zeros = np.where(db == 0)[0]
        da[zeros] = 0
        db[zeros] = 1

        self.last_a = a[..., -1:]
        self.last_b = b[..., -1:]

        return da / db


class MovingAverage(SignalFunction):
    """Returns the moving average of a signal"""

    def __init__(self, input_signal: SignalName, name: str, length: int):
        super().__init__(input_signal, name=name, params={"length": length})
        self.buffer = NumpyBuffer(maxlen=length)

    def __call__(self, x):
        output = np.zeros(x.shape)
        for i in range(x.shape[-1]):
            self.buffer.extend(x[..., i : i + 1])
            output[i] = np.mean(self.buffer.view(), axis=-1)
        return output


__all__ = [
    "Scale",
    "Sum",
    "Difference",
    "Multiply",
    "Integrate",
    "Differentiate",
    "MovingAverage",
]
