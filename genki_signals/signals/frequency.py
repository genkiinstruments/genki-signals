import numpy as np
import scipy

from genki_signals.buffers import NumpyBuffer
from genki_signals.signals.base import Signal


def upsample(signal, factor):
    # Note that we can potentially use other methods for upsampling e.g. interpolation
    return signal.repeat(factor, axis=0)


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


class WindowedSignal(Signal):
    def __init__(self, window_size, window_overlap, output_shape, default_value=0.0):
        self.win_size = window_size
        self.window_overlap = window_overlap
        self.num_to_pop = self.win_size - window_overlap
        self.input_buffer = NumpyBuffer(None)
        self.output_buffer = NumpyBuffer(None, n_cols=output_shape)
        self.output_buffer.extend(default_value * np.ones((window_size-1, *output_shape)))
        self.default_value = default_value

    def __call__(self, sig):
        self.input_buffer.extend(sig)
        while len(self.input_buffer) >= self.win_size:
            x = self.input_buffer.view(self.win_size)
            self.input_buffer.popleft(self.num_to_pop)
            out = self.windowed_fn(x)
            self.output_buffer.extend(upsample(out, self.num_to_pop))
        return self.output_buffer.popleft(len(sig))

    def windowed_fn(self, x):
        return x.sum(axis=0, keepdims=True)


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
        super().__init__(window_size, window_overlap, (self.no_buckets,), default_value=0+0j)

    def windowed_fn(self, sig):
        sig = scipy.signal.detrend(sig, type=self.detrend_type)
        sig = sig.squeeze() * self.window_fn(len(sig))  # Note this only works for 1D signals
        sig_fft = np.fft.rfft(sig) / self.win_size
        return sig_fft.reshape(1, -1)


if __name__ == '__main__':
    data = np.arange(20)
    wf = WindowedSignal(6, 2, tuple())

    wf_out = np.zeros(len(data))
    for i in range(len(data)):
        wf_out[i] = wf(data[i:i+1])

    print(wf_out)

    wf = WindowedSignal(6, 2, tuple())
    print(wf(data))

    # fft = FourierTransform("raw", "fft", window_size=256, window_overlap=0)
    # t = np.arange(1, 10, 0.01)
    # x = np.sin(2 * np.pi * 5 * t)
    # omega = np.fft.rfftfreq(256, 0.01)
    #
    # fft_out = np.zeros((len(x), 129), dtype=complex)
    # for i in range(len(x)):
    #     fft_out[i] = fft(x[i:i+1])
    #
    # psd = np.abs(fft_out)**2
    # print(omega.shape, psd.shape)
    # print(omega[psd.argmax(axis=1)])
