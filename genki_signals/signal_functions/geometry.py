from __future__ import annotations

import imufusion
import numpy as np
from ahrs.filters import Madgwick
from scipy.spatial.transform import Rotation
import logging

from genki_signals.dead_reckoning import calc_per_t_power, combine_power
from genki_signals.filters import FirFilter
from genki_signals.signal_functions.base import SignalFunction, SignalName

logger = logging.getLogger(__name__)


class Norm(SignalFunction):
    """
    Euclidian norm of a vector signal
    """

    def __init__(self, input_signal: SignalName, name: str):
        super().__init__(input_signal, name=name)

    def __call__(self, vec):
        shape = vec.shape
        return np.sqrt((vec**2).sum(axis=shape[:-1]))


class EulerOrientation(SignalFunction):
    """
    Convert quaternion representation to Euler axis/angle representation
    """

    def __init__(self, input_signal: SignalName, name: str):
        super().__init__(input_signal, name=name)

    def __call__(self, qs):
        qw = qs[0:1]
        angle = 2 * np.arccos(qw)
        norm = np.sqrt(1 - qw**2)
        normed = qs[1:] / norm
        return np.concatenate([angle * 360 / (2 * np.pi), normed], axis=0)


class EulerAngle(SignalFunction):
    """
    Convert quaternion representation to Euler angles (roll/pitch/yaw) representation
    """

    def __init__(self, input_signal: SignalName, name: str):
        super().__init__(input_signal, name=name)

    def __call__(self, qs):
        qw, qx, qy, qz = qs[0], qs[1], qs[2], qs[3]

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


class Gravity(SignalFunction):
    """
    Compute gravity vector from a quaternion orientation signal
    """

    def __init__(self, input_signal: SignalName, name: str):
        super().__init__(input_signal, name=name)

    def __call__(self, qs):
        qw, qx, qy, qz = qs[0], qs[1], qs[2], qs[3]

        grav_x = 2.0 * (qx * qz - qw * qy)
        grav_y = 2.0 * (qw * qx + qy * qz)
        grav_z = 2.0 * (qw * qw - 0.5 + qz * qz)
        return np.stack([grav_x, grav_y, grav_z])


class Rotate(SignalFunction):
    """
    Compute a rotated version of a 3D signal with a quaternion input signal
    """

    def __init__(
        self,
        input_signal: SignalName,
        orientation_signal: SignalName,
        name: str,
    ):
        super().__init__(input_signal, orientation_signal, name=name)

    def __call__(self, xs, qs):
        rot = Rotation.from_quat(qs[:, [1, 2, 3, 0]].T)
        return rot.apply(xs.T).T


def _half_plane(data: np.ndarray) -> np.ndarray:
    """Finds if a 2D vector is in the upper or lower half-plane (y-coord is positive or negative). Returns the sign

    Examples:
        >>> x = np.array([[-1, 2, 3], [2, -10, 4]])
        >>> _half_plane(x)
        array([ 1, -1,  1])
    """
    assert data.ndim == 2 and data.shape[0] == 2, f"Expected a matrix of 2D vectors. Got a matrix {data.shape=}"
    return (data[1] >= 0).astype(int) * 2 - 1


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


class OrientationXy(SignalFunction):
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

    def __init__(self, input_signal: SignalName, name: str):
        super().__init__(input_signal, name=name)
        self.xyz_org = np.array([1, 0, 0])
        self.xy_org = self.xyz_org[:2]

    def __call__(self, qs):
        rotator = qs.copy()
        # The conjugate gives us global -> local coordinate rotation
        rotator.loc[:, [0, 1, 2]] = -rotator[:, [0, 1, 2]]
        xyz = Rotation.from_quat(rotator).apply(self.xyz_org)
        xy = xyz[:, :2]
        angles = calc_angle_from_org(xy, self.xy_org)
        out = np.c_[angles, xyz]
        return out


class MadgwickOrientation(SignalFunction):
    """
    Create quaternion orientation representation from raw acc/gyro signals
    using Madgwick algorithm. Includes gyro debiasing.
    """

    def __init__(
        self,
        gyro_signal: SignalName,
        acc_signal: SignalName,
        sample_rate: float,
        name: str,
        gain: float = 0.033,
        q0: list[float] = None,
    ):
        super().__init__(
            gyro_signal, acc_signal, name=name, params={"sample_rate": sample_rate, "gain": gain, "q0": q0}
        )
        self.Q = np.array(q0 or [1.0, 0.0, 0.0, 0.0])
        self.madgwick = Madgwick(gain=gain, frequency=sample_rate, q0=self.Q)
        self.offset = imufusion.Offset(int(sample_rate))  # gyro debiasing
        self.synced = False

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
    sample_rate: int,
    mag_rejection: float = 90.0,
    acc_rejection: float = 90.0,
    rejection_timeout_sec: float = 3,
) -> imufusion.Ahrs:
    _ahrs = imufusion.Ahrs()
    _ahrs.settings = imufusion.Settings(gain, mag_rejection, acc_rejection, int(rejection_timeout_sec * sample_rate))
    return _ahrs


class OffsetIdentity:
    def update(self, x):
        return x


class FusionOrientation(SignalFunction):
    """
    Create quaternion orientation representation from raw acc/gyro signals
    using Fusion algorithm. Includes gyro debiasing.
    """

    def __init__(
        self,
        gyro_signal: SignalName,
        acc_signal: SignalName,
        sample_rate: float,
        name: str,
        gain: float = 0.5,
        use_offset: bool = True,
    ):
        super().__init__(
            gyro_signal,
            acc_signal,
            name=name,
            params={"sample_rate": sample_rate, "gain": gain, "use_offset": use_offset},
        )
        self.ahrs = ahrs(
            gain,
            sample_rate,
            mag_rejection=90.0,
            acc_rejection=90.0,
            rejection_timeout_sec=3,
        )
        self.offset = imufusion.Offset(sample_rate) if use_offset else OffsetIdentity()
        self.dt = 1 / sample_rate

    def __call__(self, gyro, acc):
        qs = np.zeros((len(gyro), 4))
        for i in range(len(qs)):
            gyro_i = self.offset.update(gyro[i])
            self.ahrs.update_no_magnetometer(gyro_i, acc[i], self.dt)
            qs[i] = self.ahrs.quaternion.array
            if np.sum(qs[i] ** 2) > 1 + 1e-3:
                logger.warn(f"Fusion orientation '{self.name}' computed invalid quaternion: {qs[i]}")
        return qs


class GravityProjection(SignalFunction):
    """
    SignalFunction to compute a projection of a 3D signal onto the 2D subspace
    orthogonal to gravity.
    """

    def __init__(
        self,
        input_signal: SignalName,
        gravity_signal: SignalName,
        name: str,
    ):
        super().__init__(input_signal, gravity_signal, name=name)
        self.qr_fact = np.vectorize(np.linalg.qr, signature="(n, m, r)->(n, m, r),(n, r, r)")

    def __call__(self, G, x):
        ones = np.ones(len(G))
        zeros = np.zeros_like(ones)
        # A is a column matrix made from two vectors that we know are
        # orthogonal to G. For the first vector, we arbitrarily choose
        # 1 and 0 for the first two components, and compute the third
        # component s.t. the vector is orthogonal to G. For the second vector, we
        # similarly 0 and 1 for the first two components. We end up with
        # the vectors [1, 0, -g_x / g_z] and [0, 1, -g_y / g_z].
        A = np.dstack([ones, zeros, zeros, ones, -G[:, 0] / G[:, 2], -G[:, 1] / G[:, 2]]).reshape(-1, 3, 2)
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


class AngleBetween(SignalFunction):
    """
    SignalFunction to compute the angle between two 2D vector signals
    """

    def __init__(self, input_a: SignalName, input_b: SignalName, name: str):
        super().__init__(input_a, input_b, name=name)

    def __call__(self, v1, v2):
        v1_norm = np.linalg.norm(v1, axis=1)
        v2_norm = np.linalg.norm(v2, axis=1)
        dot_prod = np.einsum("ij,ij->i", v1, v2)
        return np.arccos(np.clip(dot_prod / (v1_norm * v2_norm), -1, 1))


class DeadReckoning(SignalFunction):
    """Perform real time dead reckoning using acceleration and gyro"""

    def __init__(
        self,
        input_gyro: SignalName,
        input_acc: SignalName,
        name: str,
        len_sec: float,
        sample_rate: int,
        bias: float = 0.11,
        c_acc: float = 1.0,
        c_gyro: float = 1 / 300,
        beta: float = 50.0,
        threshold: float = 0.5,
        half: bool = True,
    ):
        super().__init__(
            input_gyro,
            input_acc,
            name=name,
            params={
                "len_sec": len_sec,
                "sample_rate": sample_rate,
                "bias": bias,
                "c_acc": c_acc,
                "c_gyro": c_gyro,
                "beta": beta,
                "threshold": threshold,
                "half": half,
            },
        )
        self.filter_gyro = (
            FirFilter.create_half_gaussian(len_sec, sample_rate)
            if half
            else FirFilter.create_gaussian(len_sec, sample_rate)
        )
        self.filter_linacc = (
            FirFilter.create_half_gaussian(len_sec, sample_rate)
            if half
            else FirFilter.create_gaussian(len_sec, sample_rate)
        )
        self.c_acc = c_acc
        self.c_gyro = c_gyro
        self.bias = bias
        self.beta = beta
        self.threshold = threshold

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


class ZeroCrossing(SignalFunction):
    """Returns the zero crossing of signals as 1 and otherwise 0"""

    def __init__(self, input_signal: SignalName, name: str):
        super().__init__(input_signal, name=name)
        self.state = None

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


__all__ = [
    "Norm",
    "EulerOrientation",
    "EulerAngle",
    "Gravity",
    "Rotate",
    "OrientationXy",
    "MadgwickOrientation",
    "FusionOrientation",
    "GravityProjection",
    "AngleBetween",
    "DeadReckoning",
    "ZeroCrossing",
]
