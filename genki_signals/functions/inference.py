from __future__ import annotations

import logging

import numpy as np
from onnxruntime import InferenceSession

from genki_signals.functions.base import SignalFunction, SignalName
from genki_signals.functions.windowed import WindowedSignalFunction

logger = logging.getLogger(__name__)


class Inference(SignalFunction):
    """
    Run real-time inference using an ONNX model. Operates on a single input signal, and one sample at a time.
    If stateful=True, the model is run as an RNN, and the state is passed in as a parameter and stored between calls.
    """

    def __init__(
        self,
        input_signal: SignalName,
        name: str,
        model_filename,
        stateful: bool,
        init_state=None,
    ):
        super().__init__(
            input_signal, name=name, params={"model": model_filename, "stateful": stateful, "init_state": init_state}
        )
        self.stateful = stateful
        self.state = init_state
        self.session = InferenceSession(model_filename)
        self.input_names = [inp.name for inp in self.session.get_inputs()]
        self.output_names = [out.name for out in self.session.get_outputs()]

    def __call__(self, x):
        # x shape (6, 16, t)
        x = x[np.newaxis, ..., -1]  # note doesn't work offline
        if self.stateful:
            output, self.state = self.session.run(
                self.output_names,
                {
                    self.input_names[0]: x.astype(np.float32),
                    self.input_names[1]: self.state.astype(np.float32),
                },
            )
        else:
            output = self.session.run(self.output_names, {self.input_names[0]: x.astype(np.float32)})
        return output[0][..., None]


class WindowedInference(WindowedSignalFunction, SignalFunction):
    """
    Run real-time inference using an ONNX model. Operates on a single input signal, and on a
    window of samples at a time, window_kwargs specify the windowing parameters (window_length and window_overlap).
    """
    def __init__(self, input_signal: SignalName, name: str, model_filename, **window_kwargs):
        super().__init__(input_signal, name=name, params={"model_filename": model_filename, **window_kwargs})
        self.init_windowing(**window_kwargs)
        self.session = InferenceSession(model_filename)

    def windowed_fn(self, x):
        x = x.T[np.newaxis, ...]
        output, output_extra = self.session.run(["output", "output_extra"], {"input": x.astype(np.float32)})
        return output[0]


__all__ = [
    "Inference",
    "WindowedInference",
]
