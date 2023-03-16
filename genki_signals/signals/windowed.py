from __future__ import annotations

import numpy as np
import scipy

from genki_signals.buffers import NumpyBuffer
from genki_signals.signals.base import Signal


def upsample(signal, factor):
    # Note that we can potentially use other methods for upsampling e.g. interpolation
    return signal.repeat(factor, axis=-1)


class SampleRate(Signal):
    def __init__(self, input_name: str = "timestamp", name: str = "sample_rate", unit_multiplier=1):
        self.name = name
        self.input_names = [input_name]
        self.unit_multiplier = unit_multiplier
        self.last_ts = 0

    def __call__(self, signal):
        rate = 1 / np.diff(signal, prepend=self.last_ts)
        self.last_ts = signal[-1]
        return rate * self.unit_multiplier


class WindowedSignal(Signal):
    def __init__(self, window_size: int, window_overlap: int, output_shape, default_value: float=0.0, upsample: bool=True):
        self.win_size = window_size
        self.window_overlap = window_overlap
        self.num_to_pop = self.win_size - window_overlap
        self.input_buffer = NumpyBuffer(None)
        self.output_buffer = NumpyBuffer(None, n_cols=output_shape)
        self.output_buffer.extend(default_value * np.ones((*output_shape, window_size-1)))
        self.default_value = default_value
        self.upsample = upsample

    def __call__(self, sig):
        self.input_buffer.extend(sig)
        while len(self.input_buffer) >= self.win_size:
            x = self.input_buffer.view(self.win_size)
            self.input_buffer.popleft(self.num_to_pop)
            out = self.windowed_fn(x)
            if self.upsample:
                upsampled = upsample(out, self.num_to_pop)
            else:
                upsampled = out
            self.output_buffer.extend(upsampled)
        return self.output_buffer.popleft(len(sig))

    def windowed_fn(self, x):
        raise NotImplementedError


class FourierTransform(WindowedSignal):
    """
    Computes a windowed spectrogram from a raw signal
    """
    def __init__(
            self,
            input_name :str,
            name :str,
            window_size: int = 256,
            window_overlap: int = 0,
            detrend_type: str = "linear",
            window_type: str = "hann",
            upsample: bool = False,
    ):
        self.name = name
        self.win_size = window_size
        self.no_buckets = window_size // 2 + 1
        self.input_names = [input_name]
        self.detrend_type = detrend_type
        if window_type == "hann":
            self.window_fn = scipy.signal.windows.hann
        else:
            raise ValueError(f"Unknown window type: {window_type}")
        super().__init__(window_size, window_overlap, (self.no_buckets,), default_value=0+0j, upsample=upsample)

    def windowed_fn(self, sig):
        sig = scipy.signal.detrend(sig, type=self.detrend_type)
        sig = sig * self.window_fn(sig.shape[-1])
        sig_fft = np.fft.rfft(sig) / self.win_size
        if sig_fft.ndim == 1:
            sig_fft = sig_fft[:, None]
        return sig_fft


class Delay(Signal):
    """Delays signal by n samples"""

    def __init__(self, sig_a: str, n: int, name: str=None):
        self.name = name if name is not None else "Delay"
        self.n = n
        self.input_names = [sig_a]
        self.buffer = None

    def __call__(self, sig):
        if self.buffer is None:
            self.buffer = NumpyBuffer(None, sig.shape[:-1])
            init_vals = np.zeros((self.n, *sig.shape[:-1]))
            self.buffer.extend(init_vals)

        self.buffer.extend(sig)
        out = self.buffer.popleft(len(sig))
        return out


__all__ = [
    "SampleRate",
    "WindowedSignal",
    "FourierTransform",
    "Delay",
    ]