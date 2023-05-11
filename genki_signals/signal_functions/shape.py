from __future__ import annotations

import numpy as np

from genki_signals.signal_functions.base import SignalFunction, SignalName


class ExtractDimension(SignalFunction):
    """ SignalFunction to extract a dimension from a signal """

    def __init__(self, input_signal: SignalName, name: str, dim: int | tuple[int]):
        super().__init__(input_signal, name=name, params={"dim": dim})
        self.dim = dim

    def __call__(self, v):
        return v[self.dim]


class Concatenate(SignalFunction):
    """SignalFunction to concatenate multiple signals together"""

    def __init__(self, *input_signals: SignalName, name: str, axis: int = 0):
        super().__init__(*input_signals, name=name, params={"axis": axis})
        self.axis = axis

    def __call__(self, *signals):
        to_concat = []
        for col_data in signals:
            if col_data.ndim == 1:
                to_concat.append(col_data[None])
            else:
                to_concat.append(col_data)
        return np.concatenate(to_concat, axis=self.axis)


class Stack(SignalFunction):
    """SignalFunction to stack multiple signals along a given axis"""

    def __init__(self, *input_signals: SignalName, name: str, axis: int = 0):
        super().__init__(*input_signals, name=name, params={"axis": axis})
        self.axis = axis

    def __call__(self, *signals):
        return np.stack(signals, axis=self.axis)


class Reshape(SignalFunction):
    def __init__(self, input_signal: SignalName, shape: tuple[int], name: str):
        super().__init__(input_signal, name=name, params={"shape": shape})
        self.shape = shape

    def __call__(self, v):
        time = v.shape[-1] # time axis should not be reshaped
        return v.reshape(self.shape + (time,))


__all__ = [
    "ExtractDimension",
    "Concatenate",
    "Stack",
    "Reshape",
]
