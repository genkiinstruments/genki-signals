import abc
from inspect import signature
from typing import NewType

SignalName = NewType("signal", str)

class Signal(abc.ABC):
    """

    """
    @abc.abstractmethod
    def __call__(self, *args):
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"
    
    @classmethod
    def config_json(self):
        args = []
        for arg in signature(self, follow_wrapped=True).parameters.values():
            arg_config = {
                "name": arg.name,
                "type": str(arg.annotation)
            }
            if arg.default is not arg.empty:
                arg_config["default"] = arg.default
            args.append(arg_config)
            
        return {"sig_name": self.__name__, "args": args}

    @property
    def frequency_ratio(self):
        return 1
