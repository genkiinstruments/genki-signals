from typing import Tuple

import numpy as np

from genki_signals.filters import gaussian_smooth_offline


def calc_per_t_power(x: np.ndarray) -> np.ndarray:
    """Calculate the power over multiple channels of a signal

    Examples:
        >>> y = np.array([[1.0, 2.0, 2.0], [-1.0, 1.0, np.sqrt(2)]])
        >>> calc_per_t_power(y)
        array([3., 2.])
    """
    power = np.sqrt(np.sum(x**2, axis=-1))
    return power


def sigmoid(x, beta=1.0):
    return 1 / (1 + np.exp(-x * beta))


def combine_power(
    pow_gyro: np.ndarray,
    pow_linacc: np.ndarray,
    bias: float = 0.11,
    c_acc: float = 1.0,
    c_gyro: float = 1 / 300.0,
    beta: float = 50.0,
) -> Tuple[np.ndarray, np.ndarray]:
    pow_combined = c_acc * pow_linacc + c_gyro * pow_gyro
    probability = sigmoid(pow_combined - bias, beta)
    return probability, pow_combined


def zero_velocity_from_linacc_and_gyro(
    gyro: np.ndarray,
    linacc: np.ndarray,
    sigma: float,
    bias: float = 0.11,
    c_acc: float = 1.0,
    c_gyro: float = 1 / 300,
    beta: float = 50.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """Given linear acceleration, gyro and parameters, for each timestep determine whether Wave was in motion or not

    Args:
        gyro: Gyro signal as an array
        linacc: Linear acceleration signal as an array (usually in a global coordinate system)
        sigma: Determines the size of the smoothing signal, depends on the sampling rate as well
        bias: Bias of the power for the non-linearity
        c_acc: The coefficient of the acceleration when combining the power of the acceleration signal and gyro signal
        c_gyro: The coefficient of the gyro when combining the power of the acceleration signal and gyro signal
        beta: Strength of the non-linearity in the sigmoid

    Returns:
        2 arrays, "probability" of there being movement and the combined power
    """
    pow_gyro = calc_per_t_power(gyro)
    pow_gyro = gaussian_smooth_offline(pow_gyro, sigma)

    pow_linacc = calc_per_t_power(linacc)
    pow_linacc = gaussian_smooth_offline(pow_linacc, sigma)

    probability, pow_combined = combine_power(
        pow_gyro, pow_linacc, bias, c_acc, c_gyro, beta
    )

    return probability, pow_combined
