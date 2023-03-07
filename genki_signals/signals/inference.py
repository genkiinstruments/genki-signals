import numpy as np
import torch

from genki_signals.signals import Signal


class Inference(Signal):
    """
    Run real-time inference using a torch model
    """

    def __init__(self, model, input_signals, stateful, name, init_state=None):
        self.name = name
        self.model = model
        self.input_names = input_signals
        self.stateful = stateful
        self.state = init_state

    def __call__(self, *inputs):
        to_concat = []
        for col_data in inputs:
            if col_data.ndim == 1:
                to_concat.append(col_data[:, None])
            else:
                to_concat.append(col_data)
        arr = np.concatenate(to_concat).T
        tns = torch.from_numpy(arr).float()
        if self.stateful:
            inferred_tns, self.state = self.model.inference(tns, self.state)
        else:
            inferred_tns = self.model.inference(tns)
        return inferred_tns.numpy().T
