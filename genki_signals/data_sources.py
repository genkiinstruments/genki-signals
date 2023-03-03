"""
A DataSource is an input to a SignalSystem (see old_signals.py).

DataSources are expected to collect some data into a queue, usually by
using a separate thread for writing. A concrete DataSource just needs to
implement start() and stop() for writer setup and cleanup, respectively.

The base class DataSource implements read() which gives the user all data
points that have been written to the buffer since the last call to read().
Data is returned as a list of dicts, the keys of the dicts should be consistent
across reads. The base class also implements functionality for recording data
into csv files.
"""
import abc
import sys
import datetime
import threading
import time
from pathlib import Path
from queue import Queue
from threading import Thread
import logging
from typing import Callable

import numpy as np
import pandas as pd
from genki_wave.data import DataPackage, RawDataPackage

from genki_signals.array_frame import ArrayFrame
from genki_signals.buffers import DataBuffer

logger = logging.getLogger(__name__)


class BusyThread(threading.Thread):
    """
    Opens a thread that runs a callback at a given interval.
    """

    def __init__(self, interval: int, callback: Callable, sleep_time: float = 1e-6):
        super().__init__()
        self.interval = interval
        self.callback = callback
        self._stop_event = threading.Event()
        self.sleep_time = sleep_time

    def run(self):
        while not self._stop_event.is_set():
            start_time = time.time()
            self.callback(start_time)
            sleep_end = start_time + self.interval
            while time.time() < sleep_end:
                time.sleep(self.sleep_time)

    def stop(self):
        self._stop_event.set()


class DataSource(abc.ABC):
    @abc.abstractmethod
    def start(self):
        pass

    @abc.abstractmethod
    def stop(self):
        pass

    @abc.abstractmethod
    def read(self):
        pass

    @abc.abstractmethod
    def start_listening(self):
        pass

    @abc.abstractmethod
    def read_current(self):
        pass

    def add_follower(self, follower):
        self.followers.append(follower)


# TODO: Better name for this
# it's just a DataSource? It uses a function, FunctionalDataSource?
# it uses local time as clock, LocalTimeDataSource? LocallyTimedDataSource? ManualTimerDataSource?
class LocalDataSource(DataSource):
    """
    A DataSource that generates data from a function.

    A DataSource can operate in two ways:
      * As a primary source, where a sampling rate needs to be specified, and the source generates data at the specified
      rate.
      * As a secondary source, where the source does not control the clock but can be read at any time, and will return
      the most recent value.
    """
    def __init__(self, data_fn, signal_names):
        self.busy_loop = None
        self.sample_rate = None
        self.start_time = None
        self.data_fn = data_fn
        self.buffer = Queue()
        if "timestamp" not in signal_names:
            signal_names = ["timestamp"] + signal_names
        self._signal_names = signal_names
        self.is_active = False
        self.lead = True
        self.followers = []

    def start(self, sample_rate):
        if not self.lead:
            logger.warning("Using start with a source marked as follower.")
        self.sample_rate = sample_rate
        self.is_active = True
        self.start_listening()
        for follower in self.followers:
            # TODO This is weird but only way to ensure synced start times
            follower.start_time = self.start_time
        self.busy_loop = BusyThread(1 / self.sample_rate, self._callback)
        self.busy_loop.start()

    def stop(self):
        if self.lead:
            self.busy_loop.stop()
            self.busy_loop.join()
            for follower in self.followers:
                follower.stop()
        self.is_active = False

    def _callback(self, t):
        data = self.get_data_for_time(t)
        for follower in self.followers:
            data.update(**follower.get_data_for_time(t))
        self.buffer.put(data)

    def start_listening(self):
        self.start_time = time.time()

    def read_current(self):
        if self.lead:
            logger.warning("Using read_current with a source marked as lead.")
        return self.get_data_for_time(time.time())

    def get_data_for_time(self, t):
        data = self.data_fn(t - self.start_time)
        if not isinstance(data, dict):
            data = dict(zip(self._signal_names, [t] + [data]))
        for follower in self.followers:
            data.update(**follower.get_data_for_time(t))
        return data

    def read(self):
        if not self.lead:
            logger.warning("Using read with a source marked as follower.")
        data = DataBuffer()
        while not self.buffer.empty():
            d = self.buffer.get()
            data.append(d)
        return data

    def set_follower(self):
        self.lead = False

    def set_lead(self):
        self.lead = True

    @property
    def signal_names(self):
        all_names = self._signal_names
        for follower in self.followers:
            all_names += [name for name in follower.signal_names if name != "timestamp"]
        return all_names

    def set_signal_name_postfix(self, postfix):
        self._signal_names = ["timestamp"] + [name + postfix for name in self.signal_names if name != "timestamp"]

    def add_follower(self, follower):
        self.followers.append(follower)

# =============================
# Wave
# =============================


class WaveDataSource(DataSource):
    """
    A data source to get data from a Wave. It can be either via bluetooth or
    godot connection. It can include one or more 'secondary sources', e.g.
    mouse, trackpad, keyboard, etc. In those cases, the Wave dictates the timestamp
    schedule, and the secondary sources are only checked for curent state when
    the WaveDataSource receives data.
    """

    def __init__(self, ble_address=None, godot=False):
        if ble_address is None and not godot:
            raise ValueError("Either ble_address must be provided or godot set to True.")
        self.godot = godot
        self.wave = None
        self._signal_names = None
        self.followers = []
        self.buffer = Queue()
        self.addr = ble_address
        self.latest_point = None
        self.lead = True

    def start_listening(self):
        from genki_wave.threading_runner import WaveListener

        if self.godot:
            from godot import GodotListener
            self.wave = GodotListener(callbacks=[self.process_data])
        else:
            self.wave = WaveListener(self.addr, callbacks=[self.process_data])

        for source in self.followers:
            source.start()
        self.wave.start()

    def read_current(self):
        return self.latest_point

    def read(self):
        data = DataBuffer()
        while not self.buffer.empty():
            d = self.buffer.get()
            data.append(d)
        return data

    def start(self):
        self.start_listening()

    def stop(self):
        self.wave.stop()
        for source in self.followers:
            source.stop()
        self.wave.join()

    def process_data(self, data):
        if isinstance(data, (DataPackage, RawDataPackage)):
            data = data.as_dict()
            for key, value in data.items():
                if isinstance(value, dict):
                    data[key] = np.array(list(value.values()))
            for source in self.followers:
                secondary_data = source.read_current()
                secondary_data.pop("timestamp")
                data.update(**secondary_data)
            if self._signal_names is None:
                self._signal_names = list(data.keys())

            if self.lead:
                self.buffer.put(data)
            else:
                self.latest_point = data

    def is_active(self):
        return hasattr(self, "wave") and self.wave.is_alive()

    def _repr_markdown_(self):
        active_text = "active" if self.is_active() else "not active"
        return f"{self.__class__.__name__}, **{active_text}**, address: `{self.ble_address}`"

    @property
    def signal_names(self):
        seconds_waited = 0
        while self._sigal_names is None:
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


# =============================
# Locally timed
# =============================


# TODO - implementing this is not urgent (but probably quite easy)
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


# TODO - implementing this is not urgent (but probably quite easy)
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
        super().stop()
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


# TODO - numpy is probably not the best way to store the frames, do some research
# TODO - implementing this is not urgent
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
        super().stop()
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
            self.last_frame = frame
            return data_point | {"image": frame}
        else:
            return data_point | {"image": self.last_frame}

    def read_current(self):
        return self.read()

    def signal_names(self):
        return ["timestamp", "image"]

# =============================
# DataFrame sources, how to square this with real time? Sample rate becomes lines read per second?
# What about read_current? Just read next line?
# Probably should only be available as leader, throw error if used as follower.
# =============================


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


# =============================
# Mic source, local time but specific sampling rate. Meant as a leading source. Quite different from other sources.
# Meant to be used with high sampling rate, e.g. 44100 Hz, does it even make sense to use it as a follower?
# Maybe we can have a self._is_leading attribute, raise warning if mic is started and not leading?
# =============================


class MicDataSource(DataSource):
    """Primary data source to read data from microphone."""

    def __init__(self, chunk_size=1024):
        import pyaudio

        self.pa = pyaudio.PyAudio()
        self.mic_info = self.pa.get_default_input_device_info()
        self.sample_rate = int(self.mic_info["defaultSampleRate"])
        self.format = pyaudio.paInt16
        self.chunk_size = chunk_size
        self.stream = None
        self.buffer = DataBuffer(max_size=None)
        self.is_active = False

    def start(self):

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
        self.is_active = False

    def receive(self, in_data, frame_count, time_info, status):
        from pyaudio import paContinue

        data = np.frombuffer(in_data, dtype=np.int16)
        self.buffer.extend({"audio": data[:, None]})
        return in_data, paContinue

    @property
    def signal_names(self):
        return ["audio"]

    def read(self):
        value = self.buffer.copy()
        self.buffer.clear()
        return value

    def start_listening(self):
        raise Exception("start_listening called on MicDataSource which is not intended to be used as a follower.")

    def read_current(self):
        raise Exception("read_current called on MicDataSource which is not intended to be used as a follower.")


