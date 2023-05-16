import abc
import asyncio
import threading
from queue import Queue
from typing import Callable, Type

from bleak import BleakClient, BleakScanner
from genki_wave.protocols import CommunicateCancel
from genki_wave.utils import get_or_create_event_loop

from genki_signals.buffers import DataBuffer
from genki_signals.signal_sources.base import SamplerBase, SignalSource


async def find_ble_address(device_name: str = None):
    """
        A function to find ble addresses of devices

        Args:
            device_name: The name of the device

        Returns:
            If device_name is given:
                returns ble address of device with device name: device_name
            Else:
                returns all devices
    """
    devices = await BleakScanner.discover()
    if device_name is None:
        return [device.details for device in devices]
    for device in devices:
        if device.name == device_name:
            return str(device.address)
    return None


class BLEProtocol:
    """A protocol to receive BLE packets and prepare them for the BLESignalSource"""

    def __init__(self):
        get_or_create_event_loop()
        self._queue = asyncio.Queue()

    @abc.abstractmethod
    async def packet_received(self, packet) -> None:
        """method to receive BLE packets and put each sample in self.queue"""
        pass

    @property
    def queue(self) -> asyncio.Queue:
        return self._queue


class BLESignalSource(SignalSource, SamplerBase):
    """Signal source to receive samples over a BLE connection"""

    def __call__(self):
        return self.latest_point

    def __init__(self, ble_address: str, char_uuid: str, protocol: Type[BLEProtocol], other_sources=[]):
        self.ble_address = ble_address
        self.char_uuid = char_uuid
        self.protocol = protocol
        self.sources = other_sources
        self.buffer = Queue()

    def read(self):
        data = DataBuffer()
        while not self.buffer.empty():
            sample = self.buffer.get()
            data.append(sample)
        return data

    def start(self):
        if self.is_active():
            self.stop()
        self.listener = BLEListener(self.ble_address, self.char_uuid, self.protocol, self.process_data)
        for source in self.sources:
            source.start()
        self.listener.start()

    def stop(self):
        self.listener.stop()
        for source in self.sources:
            source.stop()
        self.listener.join(timeout=1)

    def process_data(self, data):
        for source in self.sources:
            secondary_data = source.read_current()
            secondary_data.pop("timestamp", None)
            data.update(**secondary_data)
        self.buffer.put(data)
        self.latest_point = data

    def is_active(self):
        return hasattr(self, "listener") and self.listener.is_alive()

    def _repr_markdown_(self):
        active_text = "active" if self.is_active() else "not active"
        return f"{self.__class__.__name__}, **{active_text}**, address: `{self.ble_address}`"

    def __repr__(self):
        return self._repr_markdown_()


class BLEListener(threading.Thread):
    def __init__(self, ble_address, char_uuid, protocol, callback):
        self.ble_address = ble_address
        self.char_uuid = char_uuid
        self.protocol = protocol
        self.callback = callback
        super().__init__()

    def run(self):
        self.comm = CommunicateCancel()
        task = bluetooth_task(self.ble_address, self.char_uuid, self.protocol, self.comm, self.callback)
        loop = get_or_create_event_loop()
        loop.run_until_complete(task)

    def stop(self):
        self.comm.cancel = True

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop()


def protocol_as_bleak_callback_asyncio(protocol: BLEProtocol) -> Callable:
    async def _inner(sender: str, packet: bytearray) -> None:
        # NOTE: `bleak` expects a function with this signature
        await protocol.packet_received(packet)

    return _inner


async def bluetooth_task(
    ble_address: str, char_uuid: str, protocol: Type[BLEProtocol], comm: CommunicateCancel, process_data: Callable
) -> None:
    protocol = protocol()
    callback = protocol_as_bleak_callback_asyncio(protocol)
    print(f"Connecting to device at address {ble_address}")
    async with BleakClient(ble_address) as client:
        await client.start_notify(char_uuid, callback)

        print("Connected to device!")
        comm.is_connected = True
        while True:
            package = await protocol.queue.get()

            if comm.cancel:
                print("Got a cancel message, exiting.")
                comm.cancel = True
                break

            process_data(package)

        await client.stop_notify(char_uuid)
