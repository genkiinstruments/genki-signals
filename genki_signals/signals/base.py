import abc


class Signal(abc.ABC):
    """

    """
    @abc.abstractmethod
    def __call__(self, *args):
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"

    @property
    def frequency_ratio(self):
        return 1

