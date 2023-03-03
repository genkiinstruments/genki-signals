from __future__ import annotations

import warnings
from dataclasses import dataclass
from functools import wraps
from typing import Tuple

import numpy as np
from scipy import signal
from scipy.ndimage import gaussian_filter1d


def is_even(i):
    """
    >>> is_even(10), is_even(101)
    (True, False)
    """
    return i % 2 == 0


def is_odd(i):
    """
    >>> is_odd(10), is_odd(101)
    (False, True)
    """
    return not is_even(i)


@dataclass
class SosParams:
    sos: np.ndarray

    def init_zi(self):
        return signal.sosfilt_zi(self.sos)

    def freqz(self, fs):
        return signal.sosfreqz(self.sos, fs=fs)

    def as_ba(self):
        return signal.sos2tf(self.sos)

    def filter(self, x_in: float | np.ndarray, zi: np.ndarray) -> np.ndarray:
        return signal.sosfilt(self.sos, x_in, axis=0, zi=zi)

    def filter_offline(self, x: np.ndarray) -> np.ndarray:
        return signal.sosfiltfilt(self.sos, x, axis=0)


@dataclass
class BaParams:
    b: np.ndarray
    a: np.ndarray

    def init_zi(self):
        return signal.lfilter_zi(self.b, self.a)

    def freqz(self, fs):
        return signal.freqz(self.b, self.a, fs=fs)

    def as_ba(self):
        return self.b, self.a

    def filter(self, x_in: float | np.ndarray, zi: np.ndarray) -> np.ndarray:
        return signal.lfilter(self.b, self.a, x_in, axis=0, zi=zi)

    def filter_offline(self, x: np.ndarray) -> np.ndarray:
        return signal.filtfilt(self.b, self.a, x, axis=0)


def init_filter(
    filter_coeff: SosParams | BaParams, n_channels: int, x_init: np.ndarray | float
) -> np.ndarray:
    zi = filter_coeff.init_zi()
    zi = np.stack([zi] * n_channels, axis=-1)
    zi *= x_init
    return zi


def filter_response(
    filter_coeff: SosParams | BaParams, fs: float | None = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    fs = fs if fs is not None else 1.0
    w, h = filter_coeff.freqz(fs)
    angles = np.unwrap(np.angle(h))
    mag = 20 * np.log10(np.abs(h))
    return w, mag, angles


def _handle_scalar(x_in: float, n_channels: int) -> np.ndarray:
    # Single element, n_channels=1
    assert (
        n_channels == 1
    ), f"Expected `n_channels=1` when getting a scalar, got `{n_channels=}`"
    x = np.array([[x_in]])
    return x


def _handle_array(x_in: np.ndarray, n_channels: int) -> np.ndarray:
    if x_in.ndim == 1 and n_channels == 1:
        # Batch of elements with shape (n,)
        x = x_in.reshape(-1, 1)
    elif x_in.ndim == 1:
        # Single element with shape (n_channels,)
        assert (
            len(x_in) == n_channels
        ), f"Expected `{len(x_in)=}` to be the same as `{n_channels=}`"
        x = np.expand_dims(x_in, axis=0)
    elif x_in.ndim == 2:
        # Batch of elements with shape (n, n_channels)
        assert (
            x_in.shape[1] == n_channels
        ), f"Expected `{x_in.shape[1]=}` to be the same as `{n_channels=}`"
        x = x_in
    else:
        raise ValueError(f"Unsupported number of dims `{x_in.ndim=}`")
    return x


def _reshape_input(x_in: np.ndarray | float, n_channels: int) -> np.ndarray:
    """Reshape the input into a common representation, np.ndarray with shape (bs, n_channels)"""
    if isinstance(x_in, float):
        x = _handle_scalar(x_in, n_channels)
    elif isinstance(x_in, np.ndarray):
        x = _handle_array(x_in, n_channels)
    else:
        raise ValueError(f"Unsupported type {type(x_in)=}")
    return x


def _reshape_output(y: np.ndarray, x_in: np.ndarray) -> np.ndarray | float:
    """Reshape the output to have the same shape as the input"""
    if isinstance(x_in, float):
        y = float(y)
    elif y.shape != x_in.shape:
        y = y.reshape(*x_in.shape)
    return y


def reshape_input_and_output(func):
    """Decorator that handles the logic of transforming all inputs into the same format and then reverting it
    before returning the values"""

    @wraps(func)
    def _inner(self, x_in):
        x = _reshape_input(x_in, self._n_channels)
        y = func(self, x)
        y = _reshape_output(y, x_in)
        return y

    return _inner


class Filter:
    """Generic filter that works online (one/batch of samples at a time) or offline (all samples at once)

    NOTE: This assumes perfect sampling, so a user needs to resample/compensate when sampling rate drops

    Args:
        params: The filter coefficients, `SosParams` is recommended for greater numerical stability
        n_channels: Number of channels to filter. Expects column vectors
    """

    def __init__(self, params: SosParams | BaParams, n_channels: int):
        self._params = params
        self._n_channels = n_channels
        self._zi = None

    def reset(self):
        self._zi = None

    def response(self):
        fs = self._fs if hasattr(self, "_fs") else None
        return filter_response(self._params, fs)

    def as_ba(self):
        return self._params.as_ba()

    @reshape_input_and_output
    def process(self, x_in: np.ndarray | float):
        # NOTE: Expects col vectors
        if self._zi is None:
            self._zi = init_filter(self._params, self._n_channels, x_in[0])

        y, self._zi = self._params.filter(x_in, zi=self._zi)
        return y

    def process_offline(self, x: np.ndarray) -> np.ndarray:
        return self._params.filter_offline(x)


class ButterFilter(Filter):
    """Design a butterworth filter from specifications"""

    def __init__(
        self,
        order: int,
        cutoff_freq: float,
        filter_type: str,
        fs: int,
        n_channels: int = 1,
    ):
        sos = signal.butter(
            order, cutoff_freq, btype=filter_type, fs=fs, analog=False, output="sos"
        )
        super().__init__(SosParams(sos), n_channels)
        self._fs = fs
        self._cutoff_freq = cutoff_freq
        self._filter_type = filter_type
        self._order = order

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(Type={self._filter_type},"
            f"Cutoff freq={self._cutoff_freq}, Fs={self._fs}, Order={self._order})"
        )


def gaussian_kernel1d(sigma: float, truncate: float = 2.0) -> np.ndarray:
    """
    Computes a 1-D Gaussian convolution kernel.

    Adapted from private method `scipy.ndimage._gaussian_kernel1d`
    """
    sigma2 = sigma * sigma
    radius = round(sigma * truncate)
    x = np.arange(-radius, radius + 1)
    phi_x = np.exp(-0.5 / sigma2 * x**2)
    phi_x = phi_x / phi_x.sum()
    return phi_x


class FirFilter(Filter):
    """Fir filter from coefficients"""

    def __init__(self, kernel: np.ndarray, fs: int, n_channels: int = 1):
        self._fs = fs
        self.order = len(kernel)
        if not np.isclose(np.sum(kernel), 1.0):
            warnings.warn(
                "The weights of the kernel do not sum to 1.0. Usually this is not desirable."
            )
        super().__init__(BaParams(kernel, np.array([1])), n_channels)

    @classmethod
    def create_moving_average(cls, width_in_sec: float, fs: int, n_channels: int = 1):
        n = round(width_in_sec * fs)
        n = n if is_odd(n) else n + 1
        kernel = np.ones(n) / n
        return cls(kernel, fs, n_channels)

    @classmethod
    def create_gaussian(cls, width_95p_in_sec: float, fs: int, n_channels: int = 1):
        """Sigma in seconds"""
        sigma = width_95p_in_sec / 4 * fs
        kernel = gaussian_kernel1d(sigma)
        assert is_odd(len(kernel)), "Expected the length of the kernel to be odd"
        return cls(kernel, fs, n_channels)

    @classmethod
    def create_half_gaussian(
        cls, width_95p_in_sec: float, fs: int, n_channels: int = 1
    ):
        """Sigma in seconds"""
        sigma = width_95p_in_sec / 2 * fs
        kernel = gaussian_kernel1d(sigma)
        kernel = kernel[len(kernel) // 2 :]
        kernel = kernel / sum(kernel)
        assert is_odd(len(kernel)), "Expected the length of the kernel to be odd"
        return cls(kernel, fs, n_channels)

    def __repr__(self):
        return f"{self.__class__.__name__}(Fs={self._fs}, Order={self.order})"


def gaussian_smooth_offline(x: np.ndarray, sigma: float, axis=0) -> np.ndarray:
    output_dtype = float if x.dtype in (np.int32, np.int64) else None
    return gaussian_filter1d(x, sigma, mode="nearest", axis=axis, output=output_dtype)
