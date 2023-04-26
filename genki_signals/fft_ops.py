from __future__ import annotations

from functools import partial

import numpy as np
import torch
from more_itertools import pairwise
from scipy import linalg
from scipy.signal.windows import tukey
from torch import nn, Tensor


def detrend_firmware(data: np.ndarray) -> np.ndarray:
    """This detrends the same way as the firmware. This is for comparison/testing purposes to make sure it's
    consistent with the torch/numpy/scipy version

    In the other version we have
    c1 = (mean(y * x) - mean(x) * mean(y)) / (mean(x * x) - mean(x) ** 2)

    Multiplying the fraction with `size**2 / size**2` we get
    c1 = (size * sum(y * x) - sum(x) * sum(y)) / (size * sum(x * x) - sum(x) ** 2)

    Which is basically this version
    """
    size = len(data)
    size_recip = 1.0 / size
    x1, x2 = 1.0, 1.0
    a = b = c = d = e = f = 0.0
    for i in range(size):
        x1 = (i + 1) * size_recip
        a += x1 * x1
        b += x1
        c += x1
        d += x2
        e += x1 * data[i]
        f += x2 * data[i]
    determinant = a * d - b * c
    c1 = (e * d - b * f) / determinant
    c2 = (a * f - e * c) / determinant

    out = np.zeros(size, dtype=data.dtype)
    for i in range(size):
        x1 = (i + 1) * size_recip
        out[i] = data[i] - (x1 * c1 + c2)

    return out


class DetrendCustom(nn.Module):
    """Detrends the last dimension of a tensor

    Imitates the detrend operation `scipy.signal.detrend` that is used in `scipy.signal.spectrogram`
    """

    # TODO(robert): This could be performance optimized if we know the length upfront. `A`, `t` and some calculations
    #               involving `t` (mean(t)**2, mean(t * t)) could be pre-computed and re-used

    _modes = ("linear", "constant", None)

    def __init__(self, mode="linear"):
        super().__init__()
        self._mode = mode
        if self._mode not in self._modes:
            raise ValueError(f"Expected mode to be in {self._modes}, got {self._mode}")

        self._m = partial(torch.mean, dim=-1)

    def _vec_slope(self, x: Tensor, y: Tensor) -> Tensor:
        """`vectorized_slope_of_linear_fit`"""
        assert y.shape[1] == x.shape[0], f"lengths of arrays don't match {y.shape=}, {x.shape=}"
        beta = (self._m(y * x) - self._m(x) * self._m(y)) / (self._m(x * x) - self._m(x) ** 2)
        alpha = self._m(y) - beta * self._m(x)
        return torch.stack([beta, alpha])

    @staticmethod
    def _build_a(npts):
        t = torch.arange(1, npts + 1) / npts
        A = torch.stack([t, torch.ones(npts, dtype=torch.float)])
        A = A.transpose(1, 0)
        return t, A

    def _linear(self, x: Tensor) -> Tensor:
        org_dims, npts = x.shape, x.shape[-1]
        t, A = self._build_a(npts)

        x = x.reshape(-1, npts)
        coef = self._vec_slope(t, x)

        y = x - torch.matmul(A, coef).transpose(1, 0)
        y = y.reshape(org_dims)
        return y

    @staticmethod
    def _constant(x: Tensor) -> Tensor:
        return x - x.mean(dim=-1, keepdims=True)

    def forward(self, x: Tensor) -> Tensor:
        if self._mode is None:
            return x
        if self._mode == "constant":
            return self._constant(x)

        return self._linear(x)


class FftMagMatMul(nn.Module):
    """Implements rfft as a matrix multiplication for onnx export. Only works for real signals

    Calculates it over the last dimension
    """

    def __init__(self, sig_len: int):
        super().__init__()
        dft = linalg.dft(sig_len)
        dft = dft[: sig_len // 2 + 1]
        self.re = torch.from_numpy(np.real(dft)).float().transpose(1, 0)
        self.im = torch.from_numpy(np.imag(dft)).float().transpose(1, 0)

    def forward(self, x: Tensor) -> Tensor:
        re_out = torch.matmul(x, self.re)
        im_out = torch.matmul(x, self.im)
        return torch.sqrt(re_out**2 + im_out**2)


class FftMag(nn.Module):
    """Standard FFT calculations in torch over the last dimension"""

    def __init__(self):
        super().__init__()
        self.dim = -1

    def forward(self, x: Tensor) -> Tensor:
        y = torch.fft.rfft(x, dim=self.dim)
        y = torch.abs(y)
        return y


class FftCustom(nn.Module):
    """Imitates spectrogram calculations in numpy

    Calculates it over the last dimension
    """

    fft_types = ("native", "matrix")

    def __init__(self, sig_len, fs, window=None, fft_type="native"):
        super().__init__()
        self.window = window if window is not None else torch.from_numpy(tukey(sig_len, alpha=0.25, sym=False)).float()
        assert sig_len % 2 == 0, "sig_len needs to be a multiple of 2"
        assert len(self.window) == sig_len, f"{len(self.window)=} and {sig_len} need to be the same"

        self.scaling = 1 / (fs * (self.window * self.window).sum())

        if fft_type not in self.fft_types:
            raise ValueError(f"Expected `fft_type` to be in {self.fft_types}, got {fft_type}")
        self.fft = FftMag() if fft_type == "native" else FftMagMatMul(len(self.window))

    def forward(self, x):
        x_windowed = self.window * x
        x_mag = self.fft(x_windowed)
        x_psd = x_mag * x_mag
        # Taken from `spectrogram`, mode='psd'. Only the part for multiples of 2, because we ensure that the length is a
        # power of 2
        # The below is equivalent to `x_psd[..., 1:-1] *= 2`. In place multiplication is not supported by ONNX
        x_psd = torch.concat([x_psd[..., :1], 2 * x_psd[..., 1:-1], x_psd[..., -1:]], dim=-1)
        return x_psd * self.scaling


def idx_from_start_and_end(t, start, end):
    """Given an array `t`, find the indices in t corresponding to values `start` and `end` and return as a slice

    Examples:
        >>> idx_from_start_and_end(torch.tensor([5, 9.9, 10, 23, 33.1, 102.3]), 6, 30)
        slice(tensor(1), tensor(4), None)
        >>> idx_from_start_and_end(torch.tensor([5, 9.9, 10, 23, 33.1, 102.3]), 10, 33.1)
        slice(tensor(2), tensor(4), None)
    """
    idx_start = torch.where(t >= start)[0][0]
    idx_end = torch.where(t < end)[0][-1]
    return slice(idx_start, idx_end + 1)


class FftBucketizer(nn.Module):
    """Combines adjacent FFT frequencies into buckets by summing their values

    Imitates `SpectrogramFeatures._bin_spectrogram`

    Args:
        win_size: Size of the FFT window
        fs: Sampling rate
        bins: The frequency bins to calculate
        no_sum_idx: The bins that are _not_ supposed to be summarized, i.e. if a user wants to keep all the frequency
            values in a particular range
    """

    def __init__(
        self,
        win_size,
        fs,
        bins=(0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000 + 1),
        no_sum_idx=(0,),
    ):
        super().__init__()
        f = torch.fft.rfftfreq(win_size, 1 / fs)
        self._no_sum_idx = no_sum_idx
        self.slices = [idx_from_start_and_end(f, start, end) for start, end in pairwise(bins)]

    def forward(self, x: Tensor) -> Tensor:
        out = []
        for i, s in enumerate(self.slices):
            x_slice = x[..., s]
            if i not in self._no_sum_idx:
                x_slice = torch.sum(x_slice, dim=-1, keepdim=True)
            out.append(x_slice)
        return torch.concat(out, dim=-1)


def _maximum(x: Tensor, eps: Tensor) -> Tensor:
    """Imitates torch.maximum for ONNX export

    Examples:
        >>> inp = torch.tensor([[0.02, 0.00001], [0.002, 0.02]])
        >>> eps = torch.tensor(0.01)
        >>> y0 = _maximum(inp, eps)
        >>> y1 = torch.maximum(inp, eps)
        >>> (y0 == y1).all()
        tensor(True)
        >>> y0
        tensor([[0.0200, 0.0100],
                [0.0100, 0.0200]])
    """
    idxs = (x > eps).float()
    x = x * idxs
    x = x + (1 - idxs) * eps
    return x


class LogSafe(nn.Module):
    """Log computation that is safe from `log(0)` by adding an epsilon value"""

    def __init__(self, scaling: float = 10.0, eps: float = 1e-12):
        super().__init__()
        self.scaling = scaling
        self.eps = torch.tensor(eps)

    def forward(self, x: Tensor) -> Tensor:
        y = _maximum(x, self.eps)
        y = torch.log10(y)
        y = y / self.scaling
        return y


class SpectrogramFeaturesTorch(nn.Module):
    """Imitates the original `SpectrogramFeatures` that are calculated in numpy

    Allows for easier and more flexible training, no need to pre-compute all the feature, and also supports
    export to `ONNX`.

    On exporting:
        This pipeline assumes getting raw data from the accelerometer and the gyroscope as input, at a 2000Hz sampling
        rate. When exporting models to use with Wave, due to transmission restrictions of bluetooth, this raw data
        can not be sent. Therefore, some calculations need to be performed on the firmware to minimize the data that
        needs to be sent. This means that the first part of the pipeline defined in this module is calculated on the
        firmware and then the data is sent over. This means that when exporting a model, these operations need to be
        removed.

    Args:
        win_size: window size of the signals
        fs: sampling rate
        detrend_mode: what type of detrending to do, `linear`, `constant` or `None`
        log: Whether to calculate the log of the features or not
        export: Turns on export mode
    """

    def __init__(
        self,
        win_size: int,
        fs: int,
        detrend_mode: str | None,
        fft_type: str = "matrix",
        log: bool = True,
        export: bool = False,
    ):
        super().__init__()
        self.detrend = DetrendCustom(mode=detrend_mode) if not export else nn.Identity()
        self.fft = FftCustom(win_size, fs, fft_type=fft_type) if not export else nn.Identity()
        self.bucket = FftBucketizer(win_size, fs) if not export else nn.Identity()

        self.flatten = nn.Flatten(start_dim=1, end_dim=-1)
        self.log_safe = LogSafe() if log else nn.Identity()
        self.export = export

    def forward(self, x):
        x = self.detrend(x)
        x = self.fft(x)
        x = self.bucket(x)
        x = self.flatten(x)
        y = self.log_safe(x)
        return y
