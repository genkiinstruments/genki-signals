from __future__ import annotations

from genki_signals.filters import FirFilter, ButterFilter
from genki_signals.signal_functions.base import SignalFunction, SignalName


class GaussianSmooth(SignalFunction):
    """Smooths signal with a gaussian kernel"""

    def __init__(
        self,
        input_signal: SignalName,
        name: str,
        width_in_sec: float,
        sample_rate: int,
        half: bool = False,
    ):
        super().__init__(
            input_signal, name=name, params={"width_in_sec": width_in_sec, "sample_rate": sample_rate, "half": half}
        )
        self.width_in_sec = width_in_sec
        self.sample_rate = sample_rate
        self.filter = None
        self.filter_factory = FirFilter.create_half_gaussian if half else FirFilter.create_gaussian

    def __call__(self, x):
        if x.ndim == 1:
            x = x[:, None]
        if self.filter is None:
            # TODO: Make this work for other filters (n_channels), also can we abstract?
            self.filter = self.filter_factory(self.width_in_sec, self.sample_rate, n_channels=x.shape[-1])
        return self.filter.process(x).squeeze()


class HighPassFilter(SignalFunction):
    """
    High pass filter a signal. This is implemented as a butterworth filter.
    """
    def __init__(
        self,
        input_signal: SignalName,
        name: str,
        order: int,
        cutoff_freq: float,
        sample_rate: int,
    ):
        super().__init__(
            input_signal, name=name, params={"order": order, "cutoff_freq": cutoff_freq, "sample_rate": sample_rate}
        )
        self.filter = ButterFilter(order, cutoff_freq, "highpass", fs=sample_rate)

    def __call__(self, val):
        if len(val) > 0:
            return self.filter.process(val)
        return val


class BandPassFilter(SignalFunction):
    """
    Band pass filter a signal. This is implemented as a butterworth filter.
    """
    def __init__(
        self,
        input_signal: SignalName,
        name: str,
        order: int,
        cutoff_freq: float,
        sample_rate: int,
    ):
        super().__init__(
            input_signal, name=name, params={"order": order, "cutoff_freq": cutoff_freq, "sample_rate": sample_rate}
        )
        self.filter = ButterFilter(order, cutoff_freq, "bandpass", fs=sample_rate)

    def __call__(self, val):
        if len(val) > 0:
            return self.filter.process(val)
        return val


class LowPassFilter(SignalFunction):
    """
    Low pass filter a signal. This is implemented as a butterworth filter.
    """
    def __init__(
        self,
        input_signal: SignalName,
        name: str,
        order: int,
        cutoff_freq: float,
        sample_rate: int,
    ):
        super().__init__(
            input_signal, name=name, params={"order": order, "cutoff_freq": cutoff_freq, "sample_rate": sample_rate}
        )
        self.filter = ButterFilter(order, cutoff_freq, "lowpass", fs=sample_rate)

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
