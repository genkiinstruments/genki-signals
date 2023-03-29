from abc import ABC, abstractmethod

import numpy as np
import scipy

from genki_signals.buffers import NumpyBuffer, DataBuffer
from genki_signals.signals.base import Signal


def upsample(signal, factor):
    # Note that we can potentially use other methods for upsampling e.g. interpolation
    return signal.repeat(factor, axis=-1)


class SampleRate(Signal):
    def __init__(self, input_name="timestamp", name="sample_rate", unit_multiplier=1):
        self.name = name
        self.input_names = [input_name]
        self.unit_multiplier = unit_multiplier
        self.last_ts = 0

    def __call__(self, signal):
        rate = 1 / np.diff(signal, prepend=self.last_ts)
        self.last_ts = signal[-1]
        return rate * self.unit_multiplier


class WindowedSignal(Signal, ABC):
    def __init__(self, window_size, output_shape, window_overlap=0, default_value=0.0, upsample=False):
        self.win_size = window_size
        self.window_overlap = window_overlap
        self.num_to_pop = self.win_size - window_overlap
        self.input_buffer = NumpyBuffer(None)
        self.output_buffer = NumpyBuffer(None, n_cols=output_shape)
        if upsample:
            self.output_buffer.extend(default_value * np.ones((*output_shape, window_size - 1)))
        self.default_value = default_value
        self.upsample = upsample

    def __call__(self, inputs):
        self.input_buffer.extend(inputs)
        while len(self.input_buffer) >= self.win_size:
            inputs = self.input_buffer.view(self.win_size)
            self.input_buffer.popleft(self.num_to_pop)
            out = self.windowed_fn(inputs)
            if self.upsample:
                upsampled = upsample(out, self.num_to_pop)
            else:
                upsampled = out
            self.output_buffer.extend(upsampled)

        if self.upsample:
            return self.output_buffer.popleft(len(inputs))
        else:
            return self.output_buffer.popleft_all()

    @abstractmethod
    def windowed_fn(self, **inputs):
        raise NotImplementedError


class FourierTransform(WindowedSignal):
    """
    Computes a windowed spectrogram from a raw signal
    """
    def __init__(
            self,
            input_name,
            name,
            window_size=256,
            window_overlap=0,
            detrend_type="linear",
            window_type="hann",
            **kwargs
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
        super().__init__(window_size=window_size, window_overlap=window_overlap,
                         output_shape=(self.no_buckets,), default_value=0+0j, **kwargs)

    def windowed_fn(self, sig):
        sig = scipy.signal.detrend(sig, type=self.detrend_type)
        sig = sig * self.window_fn(sig.shape[-1])
        sig_fft = np.fft.rfft(sig) / self.win_size
        if sig_fft.ndim == 1:
            sig_fft = sig_fft[:, None]
        return sig_fft


class Delay(Signal):
    """Delays signal by n samples"""

    def __init__(self, sig_a, n, name=None):
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
        out = self.buffer.popleft(sig.shape[-1])
        return out
