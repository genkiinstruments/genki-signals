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
    """
    SignalFunction to concatenate multiple signals together
    """

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
    """
    SignalFunction to stack multiple signals together
    """

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
