import abc

import numpy as np
from scipy import signal


class DataSource(abc.ABC):
    @abc.abstractmethod
    def __call__(self, t):
        pass

    def start(self):
        pass

    def stop(self):
        pass


class SineWave(DataSource):
    def __init__(self, amplitude, frequency, phase):
        self.amplitude = amplitude
        self.frequency = frequency
        self.phase = phase

    def __call__(self, t):
        return self.amplitude * np.sin(2 * np.pi * self.frequency * t + self.phase)


class SquareWave(DataSource):
    def __init__(self, amplitude, frequency, phase):
        self.amplitude = amplitude
        self.frequency = frequency
        self.phase = phase

    def __call__(self, t):
        return self.amplitude * signal.square(2 * np.pi * self.frequency * t + self.phase)


class TriangleWave(DataSource):
    def __init__(self, amplitude, frequency, phase):
        self.amplitude = amplitude
        self.frequency = frequency
        self.phase = phase

    def __call__(self, t):
        return self.amplitude * signal.sawtooth(2 * np.pi * self.frequency * t + self.phase, 0.5)


class RandomNoise(DataSource):
    def __init__(self, amplitude=1):
        self.amplitude = amplitude

    def __call__(self, t):
        return self.amplitude * np.random.randn()


class MouseDataSource(DataSource):
    def __init__(self):
        import pynput
        self.mouse = pynput.mouse.Controller()

    def __call__(self, t):
        return np.array(self.mouse.position)


class KeyboardDataSource(DataSource):
    def __init__(self, keys):
        import pynput
        self.keys = keys
        self.listener = pynput.keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release
        )
        self.is_pressing = None

    def on_press(self, key):
        key_name = (
            str(key).replace("'", "").split(".")[-1]
        )  # transforms keyboard.Key and keyboard.KeyCode to strings
        if key_name in self.is_pressing:
            self.is_pressing[key_name] = 1

    def on_release(self, key):
        key_name = (
            str(key).replace("'", "").split(".")[-1]
        )  # transforms keyboard.Key and keyboard.KeyCode to strings
        if key_name in self.is_pressing:
            self.is_pressing[key_name] = 0

    def start(self):
        self.is_pressing = {k: 0 for k in self.keys}
        self.listener.start()

    def __call__(self, t):
        return {f"pressing_{key}": value for key, value in self.is_pressing.items()}
