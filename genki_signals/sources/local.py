from queue import Queue

import time
import numpy as np

from genki_signals.buffers import DataBuffer
from genki_signals.sources.base import SignalSource, SamplerBase


class MouseSource(SignalSource):
    """
    Signal source that samples the mouse position.
    """
    def __init__(self):
        import pynput

        self.mouse = pynput.mouse.Controller()

    def __call__(self):
        return np.array(self.mouse.position)


class KeyboardSource(SignalSource):
    """
    Signal source that samples whether a specified set of keys are being pressed or not.
    """
    def __init__(self, keys):
        import pynput

        self.keys = keys
        self.listener = pynput.keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.is_pressing = None

    def on_press(self, key):
        key_name = str(key).replace("'", "").split(".")[-1]  # transforms keyboard.Key and keyboard.KeyCode to strings
        if key_name in self.is_pressing:
            self.is_pressing[key_name] = 1

    def on_release(self, key):
        key_name = str(key).replace("'", "").split(".")[-1]  # transforms keyboard.Key and keyboard.KeyCode to strings
        if key_name in self.is_pressing:
            self.is_pressing[key_name] = 0

    def start(self):
        self.is_pressing = {k: 0 for k in self.keys}
        self.listener.start()

    def stop(self):
        self.listener.stop()
        self.listener.join()

    def __call__(self):
        return {f"pressing_{key}": value for key, value in self.is_pressing.items()}

    def __repr__(self):
        return f"KeyboardSource({self.keys})"


class CameraSource(SignalSource):
    """
    A SignalSource that samples frames from the camera.
    The recorded frames are in RGB format and have shape (1, height, width, 3)
    """

    def __init__(self, camera_id=0, resolution=(720, 480)):
        super().__init__()
        import cv2

        self.cv = cv2

        self.camera_id = camera_id
        self.resolution = resolution

        self.cap = None

        self.last_frame = None

    def start(self):
        if self.cap is not None:
            self.cap.release()
        self.cap = self.cv.VideoCapture(self.camera_id)

    def stop(self):
        if self.cap is not None:
            self.cap.release()

    def __call__(self):
        ret, frame = self.cap.read()
        if ret:
            frame = self.cv.resize(frame, self.resolution)
            self.last_frame = frame
            return frame
        else:
            return self.last_frame


class MicSource(SamplerBase):
    """Samples audio data in chunks from the microphone."""

    def __init__(self, key: str = "audio", chunk_size: int = 1024, followers: dict[str, SignalSource] = {}):
        import pyaudio

        self.key = key
        self.pa = pyaudio.PyAudio()
        self.mic_info = self.pa.get_default_input_device_info()
        self.sample_rate = int(self.mic_info["defaultSampleRate"])
        self.format = pyaudio.paInt16
        self.n_channels = self.mic_info["maxInputChannels"]
        self.sample_width = self.pa.get_sample_size(self.format)
        self.chunk_size = chunk_size
        self.stream = None
        self.buffer = Queue()
        self.is_active = False
        self.followers = followers
        self.signal_names = [self.key]

    def start(self):
        for source in self.followers.values():
            source.start()
        self.stream = self.pa.open(
            format=self.format,
            channels=self.mic_info["maxInputChannels"],
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self.receive,
        )
        self.stream.start_stream()
        self.is_active = True

    def stop(self):
        self.stream.stop_stream()
        self.stream.close()
        for source in self.followers.values():
            source.stop()
        self.is_active = False

    def receive(self, in_data, frame_count, time_info, status):
        # TODO: Use the info from other params somehow (particularly time_info)
        from pyaudio import paContinue

        data = {
            "timestamp": np.array([time.time()]),
            self.key: np.frombuffer(in_data, dtype=np.int16)
        }
        for name, source in self.followers.items():
            d = source()
            if isinstance(d, dict):
                d.pop("timestamp", None)
                for key, value in d.items():
                    data[f"{name}_{key}"] = np.array([value]).T
            else:
                data[name] = np.array([d]).T
        self.buffer.put(data)
        return in_data, paContinue

    def read(self):
        data = DataBuffer()
        while not self.buffer.empty():
            d = self.buffer.get()
            data.extend(d)
        return data
