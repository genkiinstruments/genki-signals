from genki_signals.buffers import DataBuffer
from genki_signals.signal_sources.base import SignalSource, SamplerBase
import numpy as np
from bleak import BleakClient
import asyncio
import struct
from queue import Queue
import time

from genki_wave.utils import get_or_create_event_loop
import threading
from genki_wave.protocols import CommunicateCancel, prepare_protocol_as_bleak_callback_asyncio
from typing import Callable

CHARACTERISTIC_UUID = "19b10001-e8f2-537e-4f6c-d104768a1214"


class ArduinoSignalSource(SignalSource, SamplerBase):
    def __call__(self):
        return self.latest_point

    def __init__(self, ble_address, other_sources=None):
        self.ble_address = ble_address
        self.sources = other_sources if other_sources is not None else []
        self.buffer = Queue()

    def read(self):
        data = DataBuffer()
        while not self.buffer.empty():
            d = self.buffer.get()
            data.append(d)
        return data

    def start(self):
        self.arduino = ArduinoListener(ble_address=self.ble_address, callback=self.process_data)
        for source in self.sources:
            source.start()
        self.arduino.start()

    def stop(self):
        self.arduino.stop()
        for source in self.sources:
            source.stop()
        self.arduino.join(timeout=1)

    def process_data(self, data):
        for source in self.sources:
            secondary_data = source.read_current()
            secondary_data.pop("timestamp", None)
            data.update(**secondary_data)
        self.buffer.put(data)
        self.latest_point = data

    def is_active(self):
        return hasattr(self, "arduino") and self.arduino.is_alive()

    def _repr_markdown_(self):
        active_text = "active" if self.is_active() else "not active"
        return f"{self.__class__.__name__}, **{active_text}**, address: `{self.ble_address}`"

    def __repr__(self):
        return self._repr_markdown_()


class ArduinoListener(threading.Thread):
    def __init__(self, ble_address, callback):
        self.ble_address = ble_address
        self.callback = callback
        super().__init__()

    def run(self):
        self.comm = CommunicateCancel()
        task = arduino_bluetooth_task(self.ble_address, self.comm, self.callback)
        loop = get_or_create_event_loop()
        loop.run_until_complete(task)

    def stop(self):
        self.comm.cancel = True

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop()


async def arduino_bluetooth_task(ble_address: str, comm: CommunicateCancel, process_data: Callable) -> None:
    protocol = ArduinoProtocol()
    callback = prepare_protocol_as_bleak_callback_asyncio(protocol)
    print(f"Connecting to Arduino at address {ble_address}")
    async with BleakClient(ble_address) as client:
        await client.start_notify(CHARACTERISTIC_UUID, callback)

        print("Connected to Arduino")
        comm.is_connected = True
        while True:
            package = await protocol.queue.get()

            if comm.cancel:
                print("Got a cancel message, exiting.")
                comm.cancel = True
                break

            process_data(package)

        await client.stop_notify(CHARACTERISTIC_UUID)


class ArduinoProtocol:
    def __init__(self):
        get_or_create_event_loop()
        self._queue = asyncio.Queue()

    async def data_received(self, data) -> None:
        values = struct.unpack("<6f", data)
        data_dict = {"timestamp": np.array(time.time()), "acc": values[:3], "gyro": values[3:]}
        await self.queue.put(data_dict)

    @property
    def queue(self) -> asyncio.Queue:
        return self._queue
