from __future__ import annotations

import numpy as np

from genki_signals.functions.base import SignalFunction, SignalName


class ExtractDimension(SignalFunction):
    """
    SignalFunction to extract a k-dimensional signal from n-dimensional signal.

    Example:
        A 3D signal with shape (10, 20, 30) can be converted to some 1D signal with shape (30,) by setting dim=(0, 0)
        for example.
    """

    def __init__(self, input_signal: SignalName, name: str, dim: int | tuple[int]):
        super().__init__(input_signal, name=name, params={"dim": dim})
        if isinstance(dim, int):
            dim = (dim,)

        self.dim = dim

    def __call__(self, v):
        if v.ndim == len(self.dim):
            raise ValueError("Cannot not convert signal to scalar")

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

        concat = np.concatenate(to_concat, axis=self.axis)

        # here we know that all np.arrays in to_concat are valid, i.e. have the same ndim atleast
        ndim = to_concat[0].ndim
        if self.axis in [-1, ndim - 1]:
            raise ValueError("Cannot concatenate along time axis")

        return concat


class Stack(SignalFunction):
    """SignalFunction to stack multiple signals along a given axis"""

    def __init__(self, *input_signals: SignalName, name: str, axis: int = 0):
        super().__init__(*input_signals, name=name, params={"axis": axis})
        self.axis = axis

    def __call__(self, *signals):
        stacked = np.stack(signals, axis=self.axis)

        # np.stack creates a new axis at the specified position, so we need to check if that new axis is the time axis
        ndim = stacked.ndim
        if self.axis in [-1, ndim - 1]:
            raise ValueError("Cannot stack along time axis")

        return stacked


class Reshape(SignalFunction):
    """SignalFunction to reshape a signal without changing the time axis"""

    def __init__(self, input_signal: SignalName, shape: tuple[int], name: str):
        super().__init__(input_signal, name=name, params={"shape": shape})
        self.shape = shape

    def __call__(self, v):
        time = v.shape[-1]
        return v.reshape(self.shape + (time,))


class Combine(SignalFunction):
    def __init__(self, signal_fns, name: str):
        self.signal_fns = signal_fns
        internal_outputs = [fn.name for fn in signal_fns]
        all_inputs = set().union(*[fn.input_signals for fn in signal_fns])
        inputs = all_inputs - set(internal_outputs)
        super().__init__(*inputs, name=name, params={"signal_fns": signal_fns})

    def __call__(self, *args):
        internal_outputs = {}
        for fn in self.signal_fns:
            fn_inputs = []
            for fn_input in fn.input_signals:
                if fn_input in internal_outputs:
                    fn_inputs.append(internal_outputs[fn_input])
                else:
                    fn_inputs.append(args[self.input_signals.index(fn_input)])
            fn_output = fn(*fn_inputs)
            internal_outputs[fn.name] = fn_output
        return internal_outputs[self.signal_fns[-1].name]


__all__ = [
    "ExtractDimension",
    "Concatenate",
    "Stack",
    "Reshape",
    "Combine"
]
