import numpy as np
from scipy import integrate

from genki_signals.buffers import NumpyBuffer
from genki_signals.signals.base import Signal


class Scale(Signal):
    def __init__(self, input_name, scale_factor, name):
        self.name = name
        self.scale_factor = scale_factor
        self.input_names = [input_name]

    def __call__(self, x):
        return x * self.scale_factor


class Sum(Signal):
    def __init__(self, input_a, input_b, name):
        self.name = name
        self.input_names = [input_a, input_b]

    def __call__(self, a, b):
        return a + b


class Difference(Signal):
    """Find the difference between 2 signals"""

    def __init__(self, input_a, input_b, name=None):
        self.name = name
        self.input_names = [input_a, input_b]

    def __call__(self, a, b):
        return a - b


class Multiply(Signal):
    def __init__(self, sig_a, sig_b, name):
        self.name = name
        self.input_names = [sig_a, sig_b]

    def __call__(self, a, b):
        return a * b


class Integrate(Signal):
    """Integrates a signal with respect to another signal (usually time)"""

    def __init__(self, sig_a, sig_b="timestamp", use_trapz=True, name=None):
        self.name = f"Int({sig_a} w.r.t. {sig_b})" if name is None else name
        self.state = 0.0
        self.trapezoid = use_trapz
        self.last_b = None
        self.input_names = [sig_a, sig_b]

    def __call__(self, a, b):
        if self.trapezoid:
            val = self.state + integrate.cumulative_trapezoid(
                y=a, x=b, initial=0.0, axis=-1
            )
        else:
            prepend_b = b[..., 0:1] if self.last_b is None else self.last_b
            db = np.diff(b, prepend=prepend_b)
            val = self.state + a.cumsum(axis=-1) * db

        if len(val) > 0:
            self.state = val[..., -1]
            self.last_b = b[..., -1:]

        return val


class Differentiate(Signal):
    """
    Differentiates a signal with respect to another signal (usually time).
    If sig_b is None, the discrete difference of sig_a is used.
    """

    def __init__(self, sig_a, sig_b="timestamp", name=None):
        self.name = (
            f"Diff({sig_a})" if sig_b is None else f"Diff({sig_a} w.r.t. {sig_b})"
        )
        self.name = name if name is not None else self.name
        self.last_a = None
        self.last_b = None
        self.input_names = [sig_a] if sig_b is None else [sig_a, sig_b]

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


class MovingAverage(Signal):
    """Returns the moving average of a signal"""

    def __init__(self, input_name, length, name):
        self.name = name
        self.buffer = NumpyBuffer(maxlen=length)
        self.input_names = [input_name]

    def __call__(self, x):
        output = np.zeros(x.shape)
        for i in range(x.shape[-1]):
            self.buffer.extend(x[..., i:i+1])
            output[i] = np.mean(self.buffer.view(), axis=-1)
        return output

