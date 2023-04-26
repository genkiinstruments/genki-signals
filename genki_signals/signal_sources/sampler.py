import threading
import time
from queue import Queue
from typing import Callable

from genki_signals.buffers import DataBuffer
from genki_signals.signal_sources.base import SamplerBase


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


class Sampler(SamplerBase):
    def __init__(
        self, sources, sample_rate, sleep_time=1e-6, timestamp_key="timestamp"
    ):
        self.sources = sources
        self.is_active = False
        self.buffer = Queue()
        self.start_time = None
        self.timestamp_key = timestamp_key
        self._busy_loop = None
        self.sample_rate = sample_rate
        self.sleep_time = sleep_time

    def start(self):
        for source in self.sources.values():
            if hasattr(source, "start"):
                source.start()
        self.start_time = time.time()
        self._busy_loop = BusyThread(
            1 / self.sample_rate, self._callback, sleep_time=self.sleep_time
        )
        self._busy_loop.start()
        self.is_active = True

    def stop(self):
        if not self.is_active:
            return
        for source in self.sources.values():
            if hasattr(source, "stop"):
                source.stop()
        self._busy_loop.stop()
        self._busy_loop.join()
        self.is_active = False

    def _callback(self, t):
        data = {self.timestamp_key: t}
        for name, source in self.sources.items():
            d = source(t - self.start_time)
            if isinstance(d, dict):
                data.update(d)
            else:
                data[name] = d
        self.buffer.put(data)

    def read(self):
        data = DataBuffer()
        while not self.buffer.empty():
            d = self.buffer.get()
            data.append(d)
        return data

    def __repr__(self):
        return f"Sampler({self.sources}, {self.sample_rate=})"
