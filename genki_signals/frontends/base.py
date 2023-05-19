from abc import ABC, abstractmethod

from genki_signals.buffers import DataBuffer
from genki_signals.system import System


class FrontendBase(ABC):
    def __init__(self, system: System):
        self.system = system
        self.system.register_data_feed(id(self), self.update)

    @abstractmethod
    def update(self, data: DataBuffer):
        pass

    def __del__(self):
        self.system.deregister_data_feed(id(self))
