import numpy as np

from genki_signals.signal_functions.base import SignalFunction, SignalName


class ExtractDimension(SignalFunction):
    """
    SignalFunction to extract a single dimension from a k-dimensional signal, i.e (k, n) -> (1, n)
    """

    def __init__(self, input_signal: SignalName, name: str, dim: int):
        super().__init__(input_signal, name=name, params={"dim": dim})
        self.dim = dim

    def __call__(self, v):
        # Slice ensures that the output is 2D i.e. (1, n)
        return v[self.dim : self.dim + 1]


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
        to_stack = []
        for col_data in signals:
            if col_data.ndim == 1:
                to_stack.append(col_data[None])
            else:
                to_stack.append(col_data)
        return np.stack(to_stack, axis=self.axis)


class Reshape(SignalFunction):
    def __init__(self, input_signal: SignalName, shape: tuple[int], name: str):
        super().__init__(input_signal, name=name, params={"shape": shape})
        self.shape = shape

    def __call__(self, v):
        return v.reshape(self.shape + (-1,))


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
