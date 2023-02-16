"""
A DataSource is an input to a SignalSystem (see signals.py).

DataSources are expected to collect some data into a queue, usually by
using a separate thread for writing. A concrete DataSource just needs to
implement start() and stop() for writer setup and cleanup, respectively.

The base class DataSource implements read() which gives the user all data
points that have been written to the buffer since the last call to read().
Data is returned as a list of dicts, the keys of the dicts should be consistent
across reads. The base class also implements functionality for recording data
into csv files.
"""
import sys
import datetime
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from queue import Queue
from threading import Thread
import logging
from typing import Callable

import numpy as np
import pandas as pd
from genki_wave.data import DataPackage, RawDataPackage

from signal_processing.array_frame import ArrayFrame

logger = logging.getLogger(__name__)


class DataSource(ABC):
    def __init__(self, rec_buffer_size=50_000):
        self.buffer = Queue()

        self.record_data = ArrayFrame()
        # Default value of 50000 is ~30MB of csv data, using prod firmware
        # and trackpad, and on 100Hz corresponds to 500s or ~8 minutes
        self.rec_buffer_size = rec_buffer_size

    @property
    def is_recording(self):
        if not hasattr(self, "_recording"):
            return False
        return self._recording

    def start_recording(self, filename):
        self._recording = True
        self.filename = filename
        self.has_written_file = False

    def _flush_to_file(self):
        df = self.record_data.as_dataframe()
        if self.has_written_file:
            df.to_csv(self.filename, header=False, index=False, mode="a")
        else:
            df.to_csv(self.filename, index=False)
            self.has_written_file = True
        self.record_data.clear()

    def stop_recording(self):
        self._flush_to_file()
        self._recording = False

    def _process_for_recording(self, data):
        return data

    def read(self):
        """
        Return all objects received since the last call to read.
        """
        items = ArrayFrame()
        cur_qsize = self.buffer.qsize()
        for _ in range(cur_qsize):
            items.append(self.buffer.get())
        if self.is_recording:
            self.record_data.extend(items)
            if len(self.record_data) >= self.rec_buffer_size:
                self._flush_to_file()
        return items

    @abstractmethod
    def start(self):
        """
        Implement setup logic for writer thread here
        """

    @abstractmethod
    def stop(self):
        """
        Implement cleanup logic for writer thread here
        """
        if self.is_recording:
            self.stop_recording()

    @abstractmethod
    def signal_names(self):
        pass


class WaveDataSource(DataSource):
    """
    A data source to get data from a Wave. It can be either via bluetooth or
    godot connection. It can include one or more 'secondary sources', e.g.
    mouse, trackpad, keyboard, etc. In those cases, the Wave dictates the timestamp
    schedule, and the secondary sources are only checked for curent state when
    the WaveDataSource receives data.
    """

    def __init__(self, ble_address=None, secondary_sources=None, godot=False):
        super().__init__()
        self.addr = ble_address
        self.godot = godot

        if secondary_sources is None:
            self.secondary = []
        elif not isinstance(secondary_sources, list):
            self.secondary = [secondary_sources]
        else:
            self.secondary = secondary_sources

    def start(self):
        from genki_wave.threading_runner import WaveListener


        if self.godot:
            from godot import GodotListener
            self.wave = GodotListener(callbacks=[self.process_data])
        else:
            self.wave = WaveListener(self.addr, callbacks=[self.process_data])

        for source in self.secondary:
            source.start()
        self.wave.start()

    def stop(self):
        self.wave.stop()
        for source in self.secondary:
            source.stop()
        self.wave.join()

    def process_data(self, data):
        if isinstance(data, (DataPackage, RawDataPackage)):
            data = data.as_dict()
            for source in self.secondary:
                secondary_data = source.read_current()
                secondary_data.pop("timestamp")
                data.update(**secondary_data)
            if not hasattr(self, "_signal_names"):
                self._signal_names = list(data.keys())
            self.buffer.put(data)

    def is_active(self):
        return hasattr(self, "wave") and self.wave.is_alive()

    def _repr_markdown_(self):
        active_text = "active" if self.is_active() else "not active"
        recording_text = ", recording" if self.is_recording else ""
        return f"{self.__class__.__name__}, **{active_text+recording_text}**, address: `{self.ble_address}`"

    def signal_names(self):
        seconds_waited = 0
        while not hasattr(self, "_signal_names"):
            logger.warn(
                f"{self.__class__.__name__} started but no package arrived, waiting."
            )
            time.sleep(1)
            seconds_waited += 1
            if seconds_waited >= 5:
                logger.error(
                    f"{self.__class__.__name__} waited for package for {seconds_waited} seconds. Exiting."
                )
                self.stop()
                sys.exit(1)
        return self._signal_names


class BusyThread(threading.Thread):
    """
    Opens a thread that runs a callback at a given interval.
    """

    def __init__(self, interval: int, callback: Callable):
        super().__init__()
        self.interval = interval
        self.callback = callback
        self._stop_event = threading.Event()

    def run(self):
        while not self._stop_event.is_set():
            start_time = time.time()
            self.callback(start_time)
            sleep_end = start_time + self.interval
            while time.time() < sleep_end:
                time.sleep(1e-6)

    def stop(self):
        self._stop_event.set()


class ManualTimerDataSource(DataSource):
    """
    A data source designed to enable data collection at a given sampling rate without
    a Wave. It can include one or more 'secondary sources', e.g. mouse,
    trackpad, keyboard, etc.
    """

    def __init__(self, sampling_rate: int, secondary_sources: list[DataSource] = None):
        super().__init__()

        self.sampling_rate = sampling_rate

        if secondary_sources is None:
            self.secondary_sources = []

        self.secondary_sources = (
            secondary_sources
            if isinstance(secondary_sources, list)
            else [secondary_sources]
        )

    def _callback(self, start_time):
        data_point = {
            "timestamp_us": start_time * 1e6,
        }
        for source in self.secondary_sources:
            source_data = source.read_current()
            source_data.pop("timestamp")
            data_point.update(**source_data)

        self.buffer.put(data_point)
        self._signal_names = list(data_point.keys())

    def start(self):
        for source in self.secondary_sources:
            source.start()

        self.busy_loop = BusyThread(1 / self.sampling_rate, self._callback)
        self.busy_loop.start()

    def stop(self):
        self.busy_loop.stop()

    def signal_names(self):
        seconds_waited = 0
        while not hasattr(self, "_signal_names"):
            logger.warn(
                f"{self.__class__.__name__} waiting to confirm secondary sources."
            )
            time.sleep(1)
            seconds_waited += 1
            if seconds_waited >= 5:
                logger.error(
                    f"{self.__class__.__name__} waited for secondary sources for {seconds_waited} seconds. Exiting."
                )
                self.stop()
                sys.exit(1)
        return self._signal_names


class MouseDataSource(DataSource):
    """
    A MouseDataSource is designed as a secondary source with WaveDataSource,
    and gives the current location of the pointer on screen.
    """

    def start(self):
        from pynput import mouse

        self.mouse = mouse.Controller()

    def stop(self):
        pass

    def read_current(self):
        x, y = self.mouse.position
        data_point = {
            "timestamp": datetime.datetime.now(),
            "mouse_pos": np.array([x, y]),
        }
        return data_point

    def signal_names(self):
        return ["timestamp", "mouse_pos"]


class KeyboardDataSource(DataSource):
    """
    A KeyboardDataSource is designed as a secondary source with WaveDataSource,
    and gives a boolean value indicating whether the keys from a given set of
    keys are being pressed or not.
    """

    def __init__(self, keys: list[str] = ["enter"]):
        self.keys = keys

    def start(self):
        from pynput import keyboard

        self.is_pressing = {k: 0 for k in self.keys}
        self.listener = keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release
        )
        self.listener.start()

    def stop(self):
        self.listener.stop()
        self.listener.join()
        super().stop()

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

    def read_current(self):
        return {"timestamp": datetime.datetime.now()} | {
            f"pressing_{key}": value for key, value in self.is_pressing.items()
        }  # Merges the dictionaries

    def signal_names(self):
        return ["timestamp"] + [f"pressing_{key}" for key in self.keys]


class EvdevTrackpadDataSource(DataSource):
    """
    An EvdevTrackpadDataSource is designed as a secondary data source for
    WaveDataSource which gives raw data from a linux trackpad instead of mouse
    data. This includes position on trackpad and whether it is currently being
    pressed.

    This prevents problems such as mouse acceleration, no movement when the mouse
    is at the edge of the screen but finger is moving, etc. and also allows us
    to detect whether the user is touching the touchpad even when the mouse is
    not moving.

    To get this to work, the running user needs to be in the `input` group.
    For example, I had to run:

        `$ sudo usermod -a -G input egill`

    And then log out and back in for the permissions to work. To find
    the udev_path for your touchpad, try running:

        `$ python -m evdev.evtest`

    If this produces no output, it is likely that you don't have the correct perms,
    that adding yourself to the group input did not work, or that you need to give
    the group read access to files in /dev/input.
    In my case, there is one line that looks like this:

        10  /dev/input/event10   DLL075B:01 06CB:76AF Touchpad       i2c-DLL075B:01

    In which case you would use /dev/input/event10 as the udev_path.
    """

    def __init__(self, udev_path, touchpad_delay=1 / 50):
        import evdev

        super().__init__()
        self.tp = evdev.InputDevice(udev_path)
        self.mouse_pos_x = self.mouse_pos_y = 0
        self.delay = touchpad_delay
        self.last_event_ts = 0

    def track_touchpad(self):
        from evdev import ecodes

        for event in self.tp.read_loop():
            if event.type == ecodes.EV_ABS and event.code == ecodes.ABS_X:
                self.mouse_pos_x = event.value
            elif event.type == ecodes.EV_ABS and event.code == ecodes.ABS_Y:
                self.mouse_pos_y = event.value
            self.last_event_ts = event.timestamp()

    def start(self):
        self.tp_thread = Thread(target=self.track_touchpad, daemon=True)
        self.tp_thread.start()
        super().start()

    def stop(self):
        super().stop()
        self.tp_thread.stop()
        self.tp_thread.join()

    def is_touching(self):
        now = datetime.datetime.now().timestamp()
        return int((now - self.last_event_ts) <= self.delay)

    def read_current(self):
        return {
            "timestamp": datetime.datetime.now(),
            "mouse_pos": np.array([self.mouse_pos_x, self.mouse_pos_y]),
            "is_touching": self.is_touching(),
        }

    def signal_names(self):
        return ["timestamp", "mouse_pos", "is_touching"]


class MacOsTrackpadDataSource(DataSource):
    """
    A trackpad data source, equivalent to EvdevTrackpadDataSource, but works on a Mac.
    """

    def __init__(self, delay=1 / 50):
        self.x = self.y = 0
        self.delay = delay
        self.last_event_ts = 0

    def contact_frame_callback(self, device, data_ptr, n_fingers, timestamp, frame):
        from pymultitouch.mtd_types import convert_touch_data

        for i in range(n_fingers):
            self.touch = convert_touch_data(frame, timestamp, data_ptr[i])
            self.x = self.touch.absolute.position.x
            self.y = self.touch.absolute.position.y
        self.last_event_ts = datetime.datetime.now().timestamp()
        return 0

    def target(self):
        from pymultitouch import mtd

        self.listener = mtd.MtdListener()
        cb = mtd.MTContactFrameCallbackFunction(self.contact_frame_callback)
        self.listener.listen(cb)

        while not self.comm.cancel:
            time.sleep(0.1)
        self.listener.unlink()

    def start(self):
        from genki_wave.threading_runner import CommunicateCancel

        self.comm = CommunicateCancel()
        self.tp_thread = Thread(target=self.target)
        self.tp_thread.start()

    def stop(self):
        self.comm.cancel = True
        self.tp_thread.join()

    def is_touching(self):
        now = datetime.datetime.now().timestamp()
        return int((now - self.last_event_ts) <= self.delay)

    def read_current(self):
        return {
            "timestamp": datetime.datetime.now(),
            "mouse_pos": np.array([self.x, -self.y]),
            "is_touching": self.is_touching(),
        }

    def signal_names(self):
        return ["timestamp", "mouse_pos", "is_touching"]


class DataFrameDataSource(DataSource):
    """
    A way to use a pandas DataFrame that has been loaded into memory as a DataSource
    """

    def __init__(self, df, lines_per_read=5):
        self.data = df
        self.lines_per_read = lines_per_read

    def start(self):
        self.current_line = 0
        self._load_chunk()

    def start_recording(self, *args):
        raise Exception(
            "Recording from {self.__class__.__name__} to a file is not supported \
                    and probably not something you want do be doing?"
        )

    def stop(self):
        super().stop()

    def _load_chunk(self):
        if self.lines_per_read < 0:
            data = self.data
        else:
            data = self.data.iloc[
                self.current_line : self.current_line + self.lines_per_read
            ]
        self.next_chunk = ArrayFrame.from_dataframe(data)

    def read(self):
        if not hasattr(self, "current_line"):
            raise Exception(
                "Tried to call read() from a data source that has not been started."
            )
        chunk = self.next_chunk
        self.current_line += len(list(chunk.values())[0])
        self._load_chunk()
        return chunk

    def signal_names(self):
        return list(self.next_chunk.keys())


class FileDataSource(DataFrameDataSource):
    def __init__(self, filename, lines_per_read=5, line_offset=0):
        self.path = Path(filename)

        if self.path.suffix == ".csv":
            data = pd.read_csv(self.path)
        elif self.path.suffix == ".pkl":
            data = pd.read_pickle(self.path)
        elif self.path.suffix == ".parquet":
            data = pd.read_parquet(self.path)
        else:
            raise Exception(
                f"Suffix {self.path.suffix} not supported for FileDataSource (Path: {self.path})"
            )
        data = data.iloc[line_offset:]
        super().__init__(data, lines_per_read)

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.path}>"

    def _repr_markdown_(self):
        return self.__repr__()


class SessionDataSource(DataFrameDataSource):
    def __init__(self, session, lines_per_read=-1):
        super().__init__(session.df, lines_per_read)


class SystemDataSource(DataSource):
    """
    A class to use a SignalSystem as a DataSource (i.e. input to another
    SignalSystem), convenient for resampling - one can e.g. define one system
    with a source at a high frequency and some derived signals, and then
    use this system, but downsampled, as a source to another system, and define
    some derived signals on this lower frequency.
    """

    def __init__(self, system, sampling_rate):
        self.system = system
        self.rate = sampling_rate

    def start(self):
        self.system.start()

    def stop(self):
        self.system.stop()

    def read(self):
        data = self.system.read()
        return self.resample_data(data)

    def resample_data(self, data):
        return data.iloc[:: self.rate]

    def signal_names(self):
        return self.system.source.signal_names() + [s.name for s in self.system.derived]


class MicDataSource(DataSource):
    """Primary data source to read data from microphone."""

    def __init__(self):
        import pyaudio

        super().__init__()
        self.pa = pyaudio.PyAudio()
        self.mic_info = self.pa.get_default_input_device_info()
        self.sampling_rate = int(self.mic_info["defaultSampleRate"])
        self.format = pyaudio.paInt16

    def start(self):
        CHUNK = 1024

        self.stream = self.pa.open(
            format=self.format,
            channels=self.mic_info["maxInputChannels"],
            rate=self.sampling_rate,
            input=True,
            frames_per_buffer=CHUNK,
            stream_callback=self.receive,
        )
        self.stream.start_stream()

    def stop(self):
        self.stream.stop_stream()
        self.stream.close()

    def receive(self, in_data, frame_count, time_info, status):
        from pyaudio import paContinue

        data = np.frombuffer(in_data, dtype=np.int16)
        self.buffer.put({"audio": data[:, None]})
        return (in_data, paContinue)

    def signal_names(self):
        return ["audio"]


class CameraDataSource(DataSource):
    """
    A class to use a camera as a secondary DataSource.
    The recorded frames are in RGB format and have shape (1, height, width, 3)
    """

    def __init__(self, camera_id=0, resolution=(640, 480)):
        super().__init__()
        import cv2

        self.cv = cv2

        self.camera_id = camera_id
        self.resolution = resolution

        self.cap = self.cv.VideoCapture(self.camera_id)
        self.last_frame = None

    def start(self):
        self.cap.open(self.camera_id)

    def stop(self):
        self.cap.release()

    def read(self):
        ret, frame = self.cap.read()
        data_point = {
            "timestamp": datetime.datetime.now(),
        }
        if ret:
            frame = self.cv.cvtColor(frame, self.cv.COLOR_BGR2RGB)
            frame = self.cv.resize(frame, self.resolution)
            frame = np.expand_dims(frame, axis=0)
            last_frame = frame
            return data_point | {"image": frame}
        else:
            return data_point | {"image": last_frame}

    def read_current(self):
        return self.read()

    def signal_names(self):
        return ["timestamp", "image"]


class RandomDataSource(DataSource):
    """Secondary data source to generate random data."""

    signal_names = ["random"]

    def start(self):
        pass

    def stop(self):
        pass

    def read_current(self):
        return {"random": np.random.rand(1, 1), "timestamp": datetime.datetime.now()}
