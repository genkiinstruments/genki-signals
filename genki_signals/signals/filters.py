from genki_signals.filters import FirFilter, ButterFilter
from genki_signals.signals.base import Signal


class GaussianSmooth(Signal):
    """Smooths signal with a gaussian kernel"""

    def __init__(
            self, sig_a, width_in_sec: float, fs: int, half: bool = False, name=None
    ):
        self.name = f"GaussianSmooth({sig_a})" if name is None else name
        self.width_in_sec = width_in_sec
        self.fs = fs
        self.filter = None
        self.filter_factory = (
            FirFilter.create_half_gaussian if half else FirFilter.create_gaussian
        )
        self.input_names = [sig_a]

    def __call__(self, x):
        if x.ndim == 1:
            x = x[:, None]
        if self.filter is None:
            # TODO: Make this work for other filters (n_channels), also can we abstract?
            self.filter = self.filter_factory(
                self.width_in_sec, self.fs, n_channels=x.shape[-1]
            )
        return self.filter.process(x).squeeze()


class HighPassFilter(Signal):
    def __init__(self, sig_a, order, cutoff_freq, fs=100, name=None):
        self.filter = ButterFilter(order, cutoff_freq, "highpass", fs=fs)
        self.name = f"HighPass({sig_a}, {cutoff_freq})" if name is None else name
        self.input_names = [sig_a]

    def __call__(self, val):
        if len(val) > 0:
            return self.filter.process(val)
        return val


class BandPassFilter(Signal):
    def __init__(self, sig_a, order, cutoff_freq, fs, name=None):
        self.filter = ButterFilter(order, cutoff_freq, "bandpass", fs=fs)
        self.name = f"BandPass({sig_a}, {cutoff_freq})" if name is None else name
        self.input_names = [sig_a]

    def __call__(self, val):
        if len(val) > 0:
            return self.filter.process(val)
        return val


class LowPassFilter(Signal):
    def __init__(self, sig_a, order, cutoff_freq, fs=100, name=None):
        self.filter = ButterFilter(order, cutoff_freq, "lowpass", fs=fs)
        self.name = f"Lowpass({sig_a}, {cutoff_freq})" if name is None else name
        self.input_names = [sig_a]

    def __call__(self, val):
        if len(val) > 0:
            return self.filter.process(val)
        return val

