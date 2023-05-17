import abc


class SignalSource(abc.ABC):
    @abc.abstractmethod
    def __call__(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass


class SamplerBase(abc.ABC):
    @abc.abstractmethod
    def start(self):
        pass

    @abc.abstractmethod
    def stop(self):
        pass

    @abc.abstractmethod
    def read(self):
        pass
