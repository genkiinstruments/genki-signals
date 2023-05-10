from abc import ABC, abstractmethod

from genki_signals.buffers import DataBuffer
from genki_signals.signal_system import SignalSystem


class FrontendBase(ABC):
    def __init__(self, system: SignalSystem):
        self.system = system
        self.system.register_data_feed(id(self), self.update)

    @abstractmethod
    def update(self, data: DataBuffer):
        pass

    def __del__(self):
        self.system.deregister_data_feed(id(self))
