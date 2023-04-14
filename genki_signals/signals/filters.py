from __future__ import annotations

from genki_signals.filters import FirFilter, ButterFilter
from genki_signals.signals.base import Signal, SignalName


class GaussianSmooth(Signal):
    """Smooths signal with a gaussian kernel"""

    def __init__(
        self,
        input_signal: SignalName,
        width_in_sec: float,
        sample_rate: int,
        half: bool = False,
        name: str = None,
    ):
        self.name = f"GaussianSmooth({input_signal})" if name is None else name
        self.width_in_sec = width_in_sec
        self.sample_rate = sample_rate
        self.filter = None
        self.filter_factory = (
            FirFilter.create_half_gaussian if half else FirFilter.create_gaussian
        )
        self.input_signals = [input_signal]

    def __call__(self, x):
        if x.ndim == 1:
            x = x[:, None]
        if self.filter is None:
            # TODO: Make this work for other filters (n_channels), also can we abstract?
            self.filter = self.filter_factory(
                self.width_in_sec, self.sample_rate, n_channels=x.shape[-1]
            )
        return self.filter.process(x).squeeze()


class HighPassFilter(Signal):
    def __init__(
        self,
        input_signal: SignalName,
        order: int,
        cutoff_freq: float,
        sample_rate: int = 100,
        name: str = None,
    ):
        self.filter = ButterFilter(
            order, cutoff_freq, "highpass", sample_rate=sample_rate
        )
        self.name = f"HighPass({input_signal}, {cutoff_freq})" if name is None else name
        self.input_signals = [input_signal]

    def __call__(self, val):
        if len(val) > 0:
            return self.filter.process(val)
        return val


class BandPassFilter(Signal):
    def __init__(
        self,
        input_signal: SignalName,
        order: int,
        cutoff_freq: float,
        sample_rate: int,
        name: str = None,
    ):
        self.filter = ButterFilter(
            order, cutoff_freq, "bandpass", sample_rate=sample_rate
        )
        self.name = f"BandPass({input_signal}, {cutoff_freq})" if name is None else name
        self.input_signals = [input_signal]

    def __call__(self, val):
        if len(val) > 0:
            return self.filter.process(val)
        return val


class LowPassFilter(Signal):
    def __init__(
        self,
        input_signal: SignalName,
        order: int,
        cutoff_freq: float,
        sample_rate: int = 100,
        name: str = None,
    ):
        self.filter = ButterFilter(
            order, cutoff_freq, "lowpass", sample_rate=sample_rate
        )
        self.name = f"Lowpass({input_signal}, {cutoff_freq})" if name is None else name
        self.input_signals = [input_signal]

    def __call__(self, val):
        if len(val) > 0:
            return self.filter.process(val)
        return val


__all__ = [
    "GaussianSmooth",
    "HighPassFilter",
    "BandPassFilter",
    "LowPassFilter",
]
