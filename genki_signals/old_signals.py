from __future__ import annotations

import logging
import math
from collections import deque
from pathlib import Path
from typing import Callable

import imufusion
import joblib
import numpy as np
import pandas as pd
import scipy.signal
import torch
from ahrs.filters import Madgwick
from more_itertools import zip_equal
from omegaconf import DictConfig, ListConfig
from scipy import integrate
from scipy.spatial.transform import Rotation

from genki_signals.system import upsample
from genki_signals.is_touching_models import StateGruInferenceOnly
from genki_signals.buffers import PandasBuffer, NumpyBuffer
from genki_signals.dead_reckoning import calc_per_t_power, combine_power
from genki_signals.filters import ButterFilter, FirFilter, gaussian_smooth_offline

logger = logging.getLogger(__name__)


class Signal:
    """
    A concrete base class for creating named transformations.

    A signal is an object that must have a 'name' attribute and
    be callable. It will be called with a DataFrame with raw
    and previously processed signals, and must return a Series
    (or a DataFrame in the case of multidimensional signals)
    with the same index.
    """

    def __init__(self, name, func):
        self.name = name
        self.func = func
        self.input_names = []

    def __call__(self, data: dict[str, np.ndarray]) -> np.ndarray:
        # TODO: what to do with this class?
        return self.func(data)

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"

    @property
    def frequency_ratio(self):
        return 1


class Norm(Signal):
    """
    Euclidian norm of a vector signal
    """

    def __init__(self, input_names, name=None):
        # TODO: Can we abstract this away?
        self.name = str(input_names) if name is None else name
        self.input_names = input_names

    def __call__(self, vec):
        return np.sqrt((vec**2).sum(axis=1))


class Difference(Signal):
    """Find the difference between 2 signals"""

    def __init__(self, sig_a, sig_b, name=None):
        self.name = f"{sig_a} - {sig_b}" if name is None else name
        self.input_names = [sig_a, sig_b]

    def __call__(self, a, b):
        return a - b


class Integrate(Signal):
    """Integrates a signal with respect to another signal (usually time)"""

    def __init__(self, sig_a, sig_b="timestamp_us", use_trapz=True, name=None):
        self.name = f"Int({sig_a} w.r.t. {sig_b})" if name is None else name
        self.state = 0.0
        self.trapezoid = use_trapz
        self.last_b = None
        self.input_names = [sig_a, sig_b]

    def __call__(self, a, b):
        if self.trapezoid:
            val = self.state + integrate.cumulative_trapezoid(
                y=a, x=b, initial=0.0, axis=0
            )
        else:
            prepend_b = b[0:1] if self.last_b is None else self.last_b
            db = np.diff(b, prepend=prepend_b, axis=0)
            val = self.state + a.cumsum(axis=0) * db

        if len(val) > 0:
            self.state = val[-1]
            self.last_b = b[-1:]

        return val


class Differentiate(Signal):
    """
    Differentiates a signal with respect to another signal (usually time).
    If sig_b is None, the discrete difference of sig_a is used.
    """

    def __init__(self, sig_a, sig_b="timestamp_us", name=None):
        self.name = (
            f"Diff({sig_a})" if sig_b is None else f"Diff({sig_a} w.r.t. {sig_b})"
        )
        self.name = name if name is not None else self.name
        self.last_a = None
        self.last_b = None
        self.input_names = [sig_a] if sig_b is None else [sig_a, sig_b]

    def __call__(self, a, b=None):
        if b is None:  # I.e. use discrete difference
            b = np.arange(len(a)).reshape(-1, 1)  # Make sure it's a column vector

        prepend_a = a[0:1] if self.last_a is None else self.last_a
        prepend_b = b[0:1] if self.last_b is None else self.last_b
        da = np.diff(a, prepend=prepend_a, axis=0)
        db = np.diff(b, prepend=prepend_b, axis=0)

        # when there is no change in b, the derivative (da/db) is set to 0
        zeros = np.where(db == 0)[0]
        da[zeros] = 0
        db[zeros] = 1

        self.last_a = a[-1:]
        self.last_b = b[-1:]

        return da / db


class MovingAverage(Signal):
    """Returns the moving average of a signal"""

    def __init__(self, sig_a, width_in_sec: float, fs: int, name=None):
        self.name = f"MovingAverage({sig_a})" if name is None else name
        self.filter = FirFilter.create_moving_average(width_in_sec, fs)
        self.input_names = [sig_a]

    def __call__(self, x):
        return self.filter.process(x)


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


class GaussianSmoothOffline(Signal):
    """Smooths signal with a gaussian kernel, useful when loading whole files at once, not for real time processing"""

    def __init__(self, sig_a, sigma: float, name=None):
        self.name = f"GaussianSmooth({sig_a})" if name is None else name
        self.sigma = sigma
        self.input_names = [sig_a]

    def __call__(self, x):
        return gaussian_smooth_offline(x, self.sigma)


class Scale(Signal):
    def __init__(self, sig_a, scale_factor, name=None):
        self.name = f"Scale({sig_a})" if name is None else name
        self.scale_factor = scale_factor
        self.input_names = [sig_a]

    def __call__(self, x):
        return x * self.scale_factor


class Inference(Signal):
    """
    Run real-time inference using a torch model
    """

    def __init__(self, model, input_signals, name):
        self.name = name
        self.model = model
        self.input_names = input_signals
        self.state = None

    def __call__(self, *inputs):
        to_concat = []
        for col_data in inputs:
            if col_data.ndim == 1:
                to_concat.append(col_data[:, None])
            else:
                to_concat.append(col_data)
        arr = np.concatenate(to_concat, axis=1)
        tns = torch.from_numpy(arr).float()
        inferred_tns, self.state = self.model.inference(tns, self.state)
        return inferred_tns.numpy()


class SamplingRate(Signal):
    def __init__(self):
        self.name = "sampling_rate"
        self.input_names = ["timestamp_us"]
        self.last_ts = 0

    def __call__(self, ts):
        if ts is None or len(ts) < 1:
            return np.zeros_like(ts)
        rate = 1 / np.diff(ts.squeeze(axis=-1), prepend=self.last_ts)
        self.last_ts = ts[-1]
        return rate.reshape(-1, 1) * 1e6  # us to s and make it a column vector


def _model_path(path: Path) -> Path:
    return path / "model.joblib"


def _config_path(path: Path) -> Path:
    return path / "config.json"


def load_model(base_path: Path | str) -> tuple:
    """
    loads the model.joblib file from the given base_path in the hierarchy:

    base_path
    |-- model.joblib
    |-- config.json

    returns a tuple of (pipeline, classifier, config)
    """
    path = Path(base_path)
    return joblib.load(_model_path(path))


class WindowedModel(Signal):
    def __init__(
        self,
        win_size: int,
        hop_length: int,
        lookback_length: int,
        output_names: list[str],
        preprocessing: Callable[[pd.DataFrame], np.ndarray],
        predict: Callable[[np.ndarray], np.ndarray],
    ):
        """WindowedModel is a signal that gets predictions from a model.

        It consists of three buffers:
            'data buffer': gathers data until it reaches the window size,
                then that data is preprocessed and fed to the lookback buffer

            'lookback buffer': gathers preprocessed data until it reaches the
                lookback length, then that data is fed to the classifier, the predictions
                upsampled and fed to the prediction buffer

            'prediction buffer': contains the final predictions from the model

        Args:
            win_size: the window size of the data buffer
            hop_length: how many samples we shift the window by each time
            lookback_length: how many windows we look back to get the input to the classifier
            output_names: the names of the outputs of the classifier
            preprocessing: a function which prepares the raw data for the classifier
            predict: the predict method of the given classifier

        Returns:
            pandas.DataFrame: The probabilities of each class and the predicted class, i.e. the one
            with the highest probability.
        """

        self.name = "windowed_model"

        self.win_size = win_size
        self.hop_length = hop_length
        self.lookback_length = lookback_length
        self.output_names = output_names

        self.data_buffer = PandasBuffer(maxlen=None, cols=None)
        self.lookback_buffer = NumpyBuffer(maxlen=None, n_cols=None)
        self.prediction_buffer = deque([0.0] * self.win_size, maxlen=None)

        self.preprocessing = preprocessing
        self.predict = predict

    @classmethod
    def from_sklearn_model(cls, model_path: str):
        """Load a model with sklearn pipeline and classifier"""
        pipeline, clf, config = load_model(model_path)

        if hasattr(clf, "verbose"):
            clf.verbose = 0

        return cls(
            win_size=config["win_size"],
            hop_length=config["hop_length"],
            lookback_length=config["lookback_length"],
            output_names=config["output_names"],
            preprocessing=lambda x: pipeline.fit_transform([x]),
            predict=lambda x: clf.predict_proba(x.reshape(1, -1)),
        )

    @classmethod
    def from_torch_model(cls, model_path: str):
        """Load a model with sklearn pipeline and torch classifier"""
        pipeline, clf, config = load_model(model_path)
        import torch

        if hasattr(clf, "verbose"):
            clf.verbose = 0

        return cls(
            win_size=config["win_size"],
            hop_length=config["hop_length"],
            lookback_length=config["lookback_length"],
            output_names=config["output_names"],
            preprocessing=lambda x: pipeline.transform([x]),
            predict=lambda x: clf.predict(torch.from_numpy(x)).detach().numpy(),
        )

    def __call__(self, data):
        """
        Feeds the raw input data to the aforementioned buffers. All predictions are 0 until
        the lookback buffer has enough data.
        """
        self.data_buffer.extend(data)
        while len(self.data_buffer) >= self.win_size:
            data_cur = self.data_buffer.view(self.win_size)
            data_cur = self.preprocessing(data_cur)
            self.lookback_buffer.extend(data_cur)
            self.data_buffer.popleft(self.hop_length)

        while len(self.lookback_buffer) >= self.lookback_length:
            x = self.lookback_buffer.view(
                self.lookback_length
            )  # (lookback_length, num_features)
            self.lookback_buffer.popleft(1)
            y = self.predict(x)  # (1, num_classes)
            y_upsampled = [
                y[0]
            ] * self.hop_length  # one prediction per window, upsample to each sample
            self.prediction_buffer.extend(y_upsampled)

        preds_cur = [
            self.prediction_buffer.popleft()
            if self.prediction_buffer
            else [0] * len(self.output_names)
            for _ in range(len(data))
        ]
        # need the if statement since predictions are only made after the lookback buffer is big enough

        if len(self.prediction_buffer) + len(self.data_buffer) > self.win_size:
            logger.warn(
                "Predictions out of sync, prediction_buffer contains old outputs"
            )

        y_pred = np.argmax(preds_cur, axis=1)
        return pd.DataFrame(
            data=np.c_[preds_cur, y_pred], columns=self.output_names + ["y_pred"]
        )


class WindowedModelTorch(Signal):
    """Runs `StateGruInferenceOnly` in real time

    Note that this returns multiple outputs as a dictionary, the actual predication and the probabilites
    for each class as returned by the model
    """

    def __init__(self, ckpt_path: str | Path):
        self.name = "is_touching_torch"
        self.input_names = ["acc", "gyro"]

        self.model = StateGruInferenceOnly.load_from_checkpoint(ckpt_path)
        self.model.freeze()

        self.win_size = self.model.win_size
        self.hop_length = self.model.hop_len
        self.output_names = [f"{self.name}_{o}" for o in self.model.classes]
        self.outputs = [self.name] + self.output_names

        self.data_buffer = NumpyBuffer(maxlen=None, n_cols=None)
        self.prediction_buffer = NumpyBuffer(maxlen=None, n_cols=len(self.output_names))
        self.prediction_buffer.extend(np.zeros((self.win_size, len(self.output_names))))

    def __call__(self, acc, gyro):
        data = np.concatenate([acc, gyro], axis=-1)
        self.data_buffer.extend(data)

        while len(self.data_buffer) >= self.win_size:
            data_cur = self.data_buffer.view(self.win_size)
            self.data_buffer.popleft(self.hop_length)

            x = torch.as_tensor(data_cur).float().transpose(1, 0).unsqueeze(0)
            y = self.model.predict(x)

            # TODO(robert): See if we can just run this on a low frequency using the new system capabilites?
            y_upsampled = upsample(
                y.numpy(), self.hop_length
            )  # one prediction per window, upsample to each sample
            self.prediction_buffer.extend(y_upsampled)

        preds_cur = self.prediction_buffer.popleft(len(data))
        preds_cur_dict = dict(zip_equal(self.output_names, preds_cur.T))

        out = {self.name: np.argmax(preds_cur, axis=1), **preds_cur_dict}
        assert len(out) == len(
            self.outputs
        ), "Expected the number of current outputs and the defined outputs to be eq."
        return out


class EulerOrientation(Signal):
    """
    Convert quaternion representation to Euler axis/angle representation
    """

    def __init__(self, input_signal="current_pose", name="orientation"):
        self.name = name
        self.input_names = [input_signal]

    def __call__(self, qs):
        qw = qs[:, 0:1]
        angle = 2 * np.arccos(qw)
        norm = np.sqrt(1 - qw**2)
        normed = qs[:, 1:] / norm
        return np.concatenate([angle * 360 / (2 * math.pi), normed], axis=1)


class EulerAngle(Signal):
    """
    Convert quaternion representation to Euler angles representation
    """

    def __init__(self, input_signal="current_pose", name=None):
        self.name = f"euler({input_signal})" if name is None else name
        self.input_names = [input_signal]

    def __call__(self, qs):
        qw, qx, qy, qz = qs[:, 0], qs[:, 1], qs[:, 2], qs[:, 3]

        # roll
        sinr = 2 * (qw * qx + qy * qz)
        cosr = 1 - 2 * (qx**2 + qy**2)
        roll = np.arctan2(sinr, cosr)

        # pitch
        sinp = 2 * (qw * qy - qz * qx)
        pitch = np.where(sinp < 1, np.arcsin(sinp), np.sign(sinp) * (np.pi / 2))

        # yaw
        siny = 2 * (qw * qz + qx * qy)
        cosy = 1 - 2 * (qy**2 + qz**2)
        yaw = np.arctan2(siny, cosy)
        return np.stack([roll, pitch, yaw])


class Gravity(Signal):
    """
    Compute gravity vector from a quaternion orientation signal
    """

    def __init__(self, input_signal="current_pose", name=None):
        self.name = f"grav({input_signal})" if name is None else name
        self.input_names = [input_signal]

    def __call__(self, qs):
        qw, qx, qy, qz = qs[:, 0], qs[:, 1], qs[:, 2], qs[:, 3]

        grav_x = 2.0 * (qx * qz - qw * qy)
        grav_y = 2.0 * (qw * qx + qy * qz)
        grav_z = 2.0 * (qw * qw - 0.5 + qz * qz)
        return np.stack([grav_x, grav_y, grav_z])


class Rotate(Signal):
    """
    Compute a rotated version of a 3D signal with a quaternion input signal
    """

    def __init__(self, signal, orientation_signal="current_pose", name=None):
        self.name = f"rotate({signal}, {orientation_signal})" if name is None else name
        self.orientation_signal = orientation_signal
        self.signal = signal
        self.input_names = [orientation_signal, signal]

    def __call__(self, qs, xs):
        rot = Rotation.from_quat(qs[:, [1, 2, 3, 0]])
        return rot.apply(xs)


def _half_plane(data: np.ndarray) -> np.ndarray:
    """Finds if a 2D vector is in the upper or lower half-plane (y-coord is positive or negative). Returns the sign

    Examples:
        >>> x = np.array([[-1, 2], [2, -10], [3, 4]])
        >>> _half_plane(x)
        array([ 1, -1,  1])
    """
    assert (
        data.ndim == 2 and data.shape[-1] == 2
    ), f"Expected a matrix of 2D vectors. Got a matrix {data.shape=}"
    return (data[:, 1] >= 0).astype(int) * 2 - 1


def calc_angle_from_org(xy_vectors: np.ndarray, xy_org: np.ndarray) -> np.ndarray:
    """Angle between multiple vectors to `xy_org`

    Note xy_org should be a unit vector

    Basically: `cos(theta) = (a dot b) / (|a| * |b|)`, implementation inspired by
    https://stackoverflow.com/a/13849249

    Examples:
        >>> org = np.array([1, 0])
        >>> xy = np.array([[1, 0], [1, 1], [1, -1], [-1, -1]])
        >>> calc_angle_from_org(xy, org)
        array([   0.,   45.,  -45., -135.])
    """
    xy_vectors = xy_vectors / np.linalg.norm(xy_vectors, axis=-1).reshape(-1, 1)
    dot_prod = xy_vectors @ xy_org
    vector_angle = np.arccos(np.clip(dot_prod, -1.0, 1.0))
    vector_angle = _half_plane(xy_vectors) * vector_angle
    return np.rad2deg(vector_angle)


class OrientationXy(Signal):
    """Angle from the initial orientation of the device to the current orientation in the xy-plane

    Algorithm description:
        1. Start with an arbitrary, but carefully selected, vector [1, 0, 0] in the global coordinate system. This
           vector corresponds to a vector that points in the direction of the quaternion [1, 0, 0, 0]
        2. Rotate this vector to be aligned with the local coordinate system
        3. Find the angle between the original vector and the new rotated vector
        4. Only look at the angle in the xy-plane

    Note on quaternion rotation:
        - Rotating using the original quaternions is a rotation: local coordinate system -> global coordinate system
        - Rotating using the conjugate quaternion is a rotation: global coordinate system -> local coordinate system
    """

    def __init__(self, orientation_signal="current_pose", name=None):
        self.name = f"XyOrientation({orientation_signal})" if name is None else name
        self.orientatation = orientation_signal

        self.xyz_org = np.array([1, 0, 0])
        self.xy_org = self.xyz_org[:2]
        self.input_names = [orientation_signal]

    def __call__(self, qs):
        rotater = qs.copy()
        # The conjugate gives us global -> local coordinate rotation
        rotater.loc[:, [0, 1, 2]] = -rotater[:, [0, 1, 2]]
        xyz = Rotation.from_quat(rotater).apply(self.xyz_org)
        xy = xyz[:, :2]
        angles = calc_angle_from_org(xy, self.xy_org)
        out = np.c_[angles, xyz]
        return out


class Linacc(Signal):
    """
    Compute linacc from gravity and acceleration
    """

    def __init__(self, acc_signal="acc", grav_signal="grav", name="linacc"):
        self.name = name
        self.input_names = [acc_signal, grav_signal]

    def __call__(self, acc, grav):
        return acc - grav


class Spectrogram(Signal):
    """
    Computes a windowed spectrogram from a raw signal
    """

    def __init__(
        self,
        sig_a,
        win_size=256,
        fft_size=256,
        win_overlap_size=0,
        fs=2000,
        fetch_x_sec=1,
    ):
        self.name = "spectrogram"

        self.win_size = win_size
        self.fft_size = fft_size

        self.no_buckets = fft_size // 2 + 1
        self.spectro_length = round(fs * fetch_x_sec / (win_size - win_overlap_size))
        self.input_names = [sig_a]
        self.num_to_pop = self.win_size - win_overlap_size
        self.input_buffer = NumpyBuffer(None, n_cols=1)

    def __call__(self, signal):
        """
        Adds data to a buffer and as soon as the buffer size is large enough, determined by `win_size`, runs
        FFT on the window of data. Usually a single value is returned for each window consisting of
        `win_size` samples, so the prediction is upsampled to `win_size` to match the length of the data
        """
        self.input_buffer.extend(signal)
        output_buffer = NumpyBuffer(None, n_cols=self.no_buckets)

        while len(self.input_buffer) >= self.win_size:
            sig = self.input_buffer.view(self.win_size)
            self.input_buffer.popleft(self.num_to_pop)

            sig = scipy.signal.detrend(sig, type="linear")
            sig = sig.squeeze() * scipy.signal.windows.hann(len(sig))
            sig = np.r_[sig, np.zeros(self.fft_size - len(sig))]
            sig_fft = np.fft.rfft(sig) / self.win_size
            sig_fft = np.abs(sig_fft)
            sig_fft = sig_fft.reshape(1, -1)
            output_buffer.extend(sig_fft)

        # self.output_buffer.popleft(len(self.output_buffer) - self.spectro_length)
        eps = 1e-20
        return np.log(np.maximum(output_buffer.view(), eps))

    @property
    def frequency_ratio(self):
        return self.win_size


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


class DeadReckoning(Signal):
    """Perform real time dead reckoning using acceleration and gyro"""

    def __init__(
        self,
        len_sec,
        fs,
        bias=0.11,
        c_acc=1.0,
        c_gyro=1 / 300,
        beta=50.0,
        prefix_gyro="gyro",
        prefix_acc="linacc_glob",
        threshold=0.5,
        half=True,
        name="DeadReckoning",
    ):
        self.name = name
        self.filter_gyro = (
            FirFilter.create_half_gaussian(len_sec, fs)
            if half
            else FirFilter.create_gaussian(len_sec, fs)
        )
        self.filter_linacc = (
            FirFilter.create_half_gaussian(len_sec, fs)
            if half
            else FirFilter.create_gaussian(len_sec, fs)
        )
        self.c_acc = c_acc
        self.c_gyro = c_gyro
        self.bias = bias
        self.beta = beta
        self.threshold = threshold
        self.input_names = [prefix_gyro, prefix_acc]

    def __call__(self, gyro, linacc):
        pow_gyro = calc_per_t_power(gyro)
        pow_gyro = self.filter_gyro.process(pow_gyro)

        pow_linacc = calc_per_t_power(linacc)
        pow_linacc = self.filter_linacc.process(pow_linacc)

        probability, pow_combined = combine_power(
            pow_gyro,
            pow_linacc,
            c_acc=self.c_acc,
            c_gyro=self.c_gyro,
            bias=self.bias,
            beta=self.beta,
        )
        return 1.0 * (probability < self.threshold)


class ZeroCrossing(Signal):
    """Returns the zero crossing of signals as 1 and non zero crossings as 0"""

    def __init__(self, sig_a, name=None):
        self.name = name if name is not None else "ZeroCrossing"
        self.state = None
        self.input_names = [sig_a]

    @staticmethod
    def _calc_curr_state(x):
        return x >= 0

    def __call__(self, xs):
        out = []
        self.state = self._calc_curr_state(xs[0]) if self.state is None else self.state
        for x in xs:
            curr_state = self._calc_curr_state(x)
            val = 0 if self.state == curr_state else 1
            out.append(val)
            self.state = curr_state
        return out


class Delay(Signal):
    """Delays signal by n samples"""

    def __init__(self, sig_a, n, name=None):
        self.name = name if name is not None else "Delay"
        self.n = n
        self.input_names = [sig_a]
        self.buffer = None

    def __call__(self, sig):
        if self.buffer is None:
            self.buffer = NumpyBuffer(None, sig.shape[1:])
            init_vals = np.zeros((self.n, *sig.shape[1:]))
            self.buffer.extend(init_vals)

        self.buffer.extend(sig)
        out = self.buffer.popleft(len(sig))
        return out


class Sum(Signal):
    def __init__(self, sig_a, sig_b, name):
        self.name = name
        self.input_names = [sig_a, sig_b]

    def __call__(self, a, b):
        return a + b


class Multiply(Signal):
    def __init__(self, sig_a, sig_b, name):
        self.name = name
        self.input_names = [sig_a, sig_b]

    def __call__(self, a, b):
        return a * b


class MadgwickOrientation(Signal):
    """
    Create quaternion orientation representation from raw acc/gyro signals
    using Madgwick algorithm. Includes gyro debiasing.
    """

    def __init__(
        self,
        fs=100.0,
        q0=np.array([1.0, 0.0, 0.0, 0.0]),
        gyro_cols="gyro",
        acc_cols="acc",
        name="madgwick",
    ):
        self.Q = q0
        self.madgwick = Madgwick(gain=0.033, frequency=fs, q0=q0)
        self.offset = imufusion.Offset(int(fs))  # gyro debiasing
        self.name = name
        self.synced = False
        self.input_names = [gyro_cols, acc_cols]

    def __call__(self, gyro, acc):
        acc = acc * 9.8
        qs = np.zeros((len(acc), 4))
        for i in range(len(acc)):
            gyro_i = self.offset.update(gyro[i]) / 180 * np.pi
            self.Q = self.madgwick.updateIMU(self.Q, gyro_i, acc[i])
            qs[i] = self.Q
        return qs


def ahrs(
    gain: float,
    fs: int,
    mag_rejection: float = 90.0,
    acc_rejection: float = 90.0,
    rejection_timeout_sec: float = 3,
) -> imufusion.Ahrs:
    _ahrs = imufusion.Ahrs()
    _ahrs.settings = imufusion.Settings(
        gain, mag_rejection, acc_rejection, int(rejection_timeout_sec * fs)
    )
    return _ahrs


class OffsetIdentity:
    def update(self, x):
        return x


class FusionOrientation(Signal):
    """
    Create quaternion orientation representation from raw acc/gyro signals
    using Fusion algorithm. Includes gyro debiasing.
    """

    def __init__(
        self,
        fs=100,
        gyro_cols="gyro",
        acc_cols="acc",
        gain=0.5,
        use_offset=True,
        name="fusion",
    ):
        self.ahrs = ahrs(
            gain, fs, mag_rejection=90.0, acc_rejection=90.0, rejection_timeout_sec=3
        )
        self.offset = imufusion.Offset(fs) if use_offset else OffsetIdentity()
        self.name = name
        self.dt = 1 / fs
        self.input_names = [gyro_cols, acc_cols]

    def __call__(self, gyro, acc):
        qs = np.zeros((len(gyro), 4))
        for i in range(len(qs)):
            gyro_i = self.offset.update(gyro[i])
            self.ahrs.update_no_magnetometer(gyro_i, acc[i], self.dt)
            qs[i] = self.ahrs.quaternion.array
            if np.sum(qs[i] ** 2) > 1 + 1e-3:
                logger.warn(
                    f"Fusion orientation '{self.name}' computed invalid quaternion: {qs[i]}"
                )
        return qs


class MouseControl(Signal):
    """Control the mouse using any signal

    Args:
        sig_x: Signal to control x direction
        sig_y: Signal to control y direction
        c_x: Scaling of signal in x direction
        c_y: Scaling of signal in y direction
        name: Name of signal. If `None` uses default.
    """

    def __init__(self, sig_x, c_x, c_y, accel_type="none", name="mouse_control"):
        from pynput.mouse import Controller

        self.name = name

        self.mouse = Controller()
        self.c_x, self.c_y = c_x, c_y

        accel_fns = {"none": lambda speed, x: x, "linear": lambda speed, x: speed * x}
        self.accel_fn = accel_fns[accel_type]
        self.input_names = [sig_x]

    def __call__(self, ps):
        speed = np.sqrt((ps**2).sum(axis=1, keepdims=True))
        ps = self.accel_fn(speed, ps)
        for x, y in ps:
            self.mouse.move(round(self.c_x * x), round(self.c_y * y))
        return np.zeros(len(ps))


class GravityProjection(Signal):
    """
    Signal to compute a projection of a 3D signal onto the 2D subspace
    orthogonal to gravity.
    """

    def __init__(
        self, signal_to_project, gravity_signal="grav", name="grav_projection"
    ):
        self.qr_fact = np.vectorize(
            np.linalg.qr, signature="(n, m, r)->(n, m, r),(n, r, r)"
        )
        self.name = name
        self.input_names = [self.signal, self.grav]

    def __call__(self, G, x):
        ones = np.ones(len(G))
        zeros = np.zeros_like(ones)
        # A is a column matrix made from two vectors that we know are
        # orthogonal to G. For the first vector, we arbitrarily choose
        # 1 and 0 for the first two components, and compute the third
        # component s.t. the vector is orthogonal to G. For the second vector, we
        # similarly 0 and 1 for the first two components. We end up with
        # the vectors [1, 0, -g_x / g_z] and [0, 1, -g_y / g_z].
        A = np.dstack(
            [ones, zeros, zeros, ones, -G[:, 0] / G[:, 2], -G[:, 1] / G[:, 2]]
        ).reshape(-1, 3, 2)
        # The QR factorization of A gives us Q, a 3x2 matrix with orthogonal
        # columns that span the subspace orthogonal to G.
        Qv, Rv = self.qr_fact(A)
        # P, the 2x3 projection matrix onto the subspace, is the inverse of Q
        # (since Q has orthogonal columns, the inverse is the same as the transpose)
        P = Qv.transpose(0, 2, 1)
        # Batch matrix multiplication - P is a sequence of 2x3 matrices,
        # and x is a sequence of 3x1 vectors. We compute P[i] @ x[i] for each i.
        X_P = np.einsum("Bij,Bj->Bi", P, x)
        return X_P[:, 1:0]  # Swap names for consistency with x/y on trackpad


class AngleBetween(Signal):
    """
    Signal to compute the angle between two 2D vector signals
    """

    def __init__(self, signal_1, signal_2, name=None):
        self.name = name if name is not None else f"angle_{signal_1}_{signal_2}"
        self.input_names = [self.signal_1, self.signal_2]

    def __call__(self, v1, v2):
        v1_norm = np.linalg.norm(v1, axis=1)
        v2_norm = np.linalg.norm(v2, axis=1)
        dot_prod = np.einsum("ij,ij->i", v1, v2)
        return np.arccos(np.clip(dot_prod / (v1_norm * v2_norm), -1, 1))


class ExtractDimension(Signal):
    """
    Signal to extract a single dimension from a k-dimensional signal, i.e (n, k) -> (n, 1)
    """

    def __init__(self, signal, dim, name=None):
        self.name = name if name is not None else f"{signal}_{dim}"
        self.dim = dim

        self.input_names = [signal]

    def __call__(self, v):
        # Slice ensures that the output is 2D i.e. (n, 1)
        return v[:, self.dim : self.dim + 1]


SIGNAL_NAMES = {
    "Difference": Difference,
    "Integrate": Integrate,
    "Differentiate": Differentiate,
    "MovingAverage": MovingAverage,
    "GaussianSmooth": GaussianSmooth,
    "GaussianSmoothOffline": GaussianSmoothOffline,
    "Scale": Scale,
    "Inference": Inference,
    "WindowedModel": WindowedModel,
    "SamplingRate": SamplingRate,
    "EulerOrientation": EulerOrientation,
    "HighPassFilter": HighPassFilter,
    "DeadReckoning": DeadReckoning,
    "Multiply": Multiply,
    "MouseControl": MouseControl,
    "Delay": Delay,
    "ZeroCrossing": ZeroCrossing,
    "FusionOrientation": FusionOrientation,
    "MadgwickOrientation": MadgwickOrientation,
    "Gravity": Gravity,
    "Rotate": Rotate,
    "GravityProjection": GravityProjection,
    "AngleBetween": AngleBetween,
    "OrientationXy": OrientationXy,
    "ExtractDimension": ExtractDimension,
}


def signal_factory(signal_kwargs: DictConfig) -> Signal:
    if not isinstance(signal_kwargs, (DictConfig, dict)):
        raise ValueError(
            f"Expected to get dictionary specifying a signal and kwargs, "
            f"got {signal_kwargs} with type {type(signal_kwargs)}"
        )
    if "class" not in signal_kwargs:
        raise ValueError(
            f"Expected to find the key 'class' in signal_kwargs, found {signal_kwargs.keys()}"
        )
    kwargs = dict(signal_kwargs)
    klass = SIGNAL_NAMES[kwargs.pop("class")]
    return klass(**kwargs)


def parse_signal_conf(conf: list[dict] | ListConfig) -> list[Signal]:
    return [signal_factory(s) for s in conf]
