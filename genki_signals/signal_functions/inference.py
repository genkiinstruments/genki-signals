from __future__ import annotations

import logging
from functools import partial
from typing import Callable

import numpy as np
import torch
from onnxruntime import InferenceSession

from genki_signals.post_processing import (
    prepare_predictions,
    group_dist_heuristic,
    GroupTracker,
)
from genki_signals.signal_functions.base import SignalFunction, SignalName
from genki_signals.signal_functions.windowed import WindowedSignalFunction

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

    def __call__(self, x):
        # x shape (6, 16, t)
        x = x[np.newaxis, ..., -1]  # note doesn't work offline
        if self.stateful:
            output, self.state = self.session.run(
                ["output", "output_state"],
                {
                    "input": x.astype(np.float32),
                    "input_state": self.state.astype(np.float32),
                },
            )
        else:
            output, output_extra = self.session.run(["output", "output_extra"], {"input": x.astype(np.float32)})
        return output[0, ..., None]


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


class ObjectTracker(WindowedSignalFunction):
    """
    Run object tracking with the output of a WindowedInference signal function.
    This SignalFunction may have side effects, and cannot be serialized. The
    callback is called once for each new object detected.
    """
    def __init__(self, input_signal: SignalName, name: str, callback: Callable, **kwargs):
        super().__init__(input_signal, name=name, params={"callback": callback, **kwargs})
        self.init_windowing(**kwargs)
        self.callback = callback

        min_group_size, min_trigger_idx = (3, 8)
        max_disappeared = 3
        dist_func = partial(group_dist_heuristic, match_lower_or_eq_idx=True, enforce_key=False)
        self._tracker = GroupTracker(dist_func, max_disappeared, min_group_size, min_trigger_idx)

    def windowed_fn(self, x):
        output = torch.tensor(x[None])
        groups = prepare_predictions(output, confidence=0.9, confidence_low=0.5)
        _, new_groups = self._tracker.update(groups)

        for g in new_groups:
            self.callback(g.key)
        return output[0].numpy()


__all__ = [
    "Inference",
    "WindowedInference",
    "ObjectTracker",
]
