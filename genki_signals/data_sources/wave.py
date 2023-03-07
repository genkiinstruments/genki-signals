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
import logging
import sys
import time
from queue import Queue

import numpy as np
from genki_wave.data import DataPackage, RawDataPackage

from genki_signals.buffers import DataBuffer
from genki_signals.data_sources.base import DataSource, SamplerBase

logger = logging.getLogger(__name__)


class WaveDataSource(DataSource, SamplerBase):
    """
    A data source to get data from a Wave. It can be either via bluetooth or
    godot connection. It can include one or more 'secondary sources', e.g.
    mouse, trackpad, keyboard, etc. In those cases, the Wave dictates the timestamp
    schedule, and the secondary sources are only checked for curent state when
    the WaveDataSource receives data.
    """

    def __call__(self, t):
        return self.latest_point

    def __init__(self, ble_address=None, godot=False):
        if ble_address is None and not godot:
            raise ValueError("Either ble_address must be provided or godot set to True.")
        self.godot = godot
        self.wave = None
        self._signal_names = None
        self.followers = []
        self.buffer = Queue()
        self.ble_address = ble_address
        self.latest_point = None
        self.lead = True

    def read(self):
        data = DataBuffer()
        while not self.buffer.empty():
            d = self.buffer.get()
            data.append(d)
        return data

    def start(self):
        from genki_wave.threading_runner import WaveListener

        if self.godot:
            from godot import GodotListener
            self.wave = GodotListener(callbacks=[self.process_data])
        else:
            self.wave = WaveListener(self.ble_address, callbacks=[self.process_data])

        for source in self.followers:
            source.start()
        self.wave.start()

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
                secondary_data.pop("timestamp", None)
                data.update(**secondary_data)
            if self._signal_names is None:
                self._signal_names = list(data.keys())

            self.buffer.put(data)
            self.latest_point = data

    def is_active(self):
        return hasattr(self, "wave") and self.wave.is_alive()

    def _repr_markdown_(self):
        active_text = "active" if self.is_active() else "not active"
        return f"{self.__class__.__name__}, **{active_text}**, address: `{self.ble_address}`"

    def __repr__(self):
        return self._repr_markdown_()

    @property
    def signal_names(self):
        seconds_waited = 0
        while self._signal_names is None:
            logger.warning(
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
