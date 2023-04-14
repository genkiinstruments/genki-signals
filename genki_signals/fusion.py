import numpy as np


class OffsetGyro:
    """
    Re-implementation of `imufusion.Offset` in Python. The original has fixed parameters, this allows us to tune the
    parameters and have full control over the algorithm. Additionally this one is simpler to understand.

    See original:
    https://github.com/xioTechnologies/Fusion/blob/main/Fusion/FusionOffset.c
    """

    def __init__(
        self, sampling_rate, cutoff_freq=0.02, timeout_const=5.0, threshold=3.0
    ):
        self._filter_coeff = cutoff_freq * 2.0 * np.pi / sampling_rate
        self._timeout = timeout_const * sampling_rate
        self._timer = 0
        self._offset = np.zeros(3)
        self._threshold = threshold

    def update(self, gyro_in):
        gyro = gyro_in - self._offset
        if np.any(np.abs(gyro) > self._threshold):
            self._timer = 0
        elif self._timer < self._timeout:
            self._timer += 1
        else:
            self._offset = self._offset + gyro * self._filter_coeff
        return gyro
