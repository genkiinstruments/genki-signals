import abc
from inspect import signature
from typing import NewType

SignalName = NewType("signal", str)


class SignalFunction(abc.ABC):
    def __init__(self, *input_signals: SignalName, name: str, params: dict = {}):
        self.name = name
        self.input_signals = input_signals
        self.params = params

    @abc.abstractmethod
    def __call__(self, *args):
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}, inputs: {self.input_signals}, params: {self.params}>"

    @classmethod
    def config_json(cls):
        args = []
        for arg in signature(cls, follow_wrapped=True).parameters.values():
            arg_config = {"name": arg.name, "type": str(arg.annotation)}
            if arg.default is not arg.empty:
                arg_config["default"] = arg.default
            args.append(arg_config)

        return {"sig_name": cls.__name__, "args": args}

    @property
    def frequency_ratio(self):
        return 1
