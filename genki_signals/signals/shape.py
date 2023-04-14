import numpy as np

from genki_signals.signals.base import Signal, SignalName


class ExtractDimension(Signal):
    """
    Signal to extract a single dimension from a k-dimensional signal, i.e (k, n) -> (1, n)
    """

    def __init__(self, input_signal: SignalName, dim: int, name: str = None):
        self.name = f"{input_signal}[{dim}]" if name is None else name
        self.dim = dim

        self.input_signals = [input_signal]

    def __call__(self, v):
        # Slice ensures that the output is 2D i.e. (1, n)
        return v[self.dim : self.dim + 1]


class Concatenate(Signal):
    """
    Signal to concatenate multiple signals together
    """

    def __init__(self, input_signals: list[SignalName], name: str):
        self.name = name
        self.input_signals = input_signals

    def __call__(self, *signals):
        to_concat = []
        for col_data in signals:
            if col_data.ndim == 1:
                to_concat.append(col_data[None])
            else:
                to_concat.append(col_data)
        return np.concatenate(to_concat, axis=0)


class Reshape(Signal):
    def __init__(self, input_signal: SignalName, shape: tuple[int], name: str):
        self.name = name
        self.shape = shape
        self.input_signals = [input_signal]

    def __call__(self, v):
        return v.reshape(self.shape + (-1,))
