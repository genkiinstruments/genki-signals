from abc import ABC, abstractmethod

import numpy as np
from flask import Flask
from flask_socketio import SocketIO

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


class WebFrontend(FrontendBase):
    def __init__(self, system: SignalSystem, port):
        super().__init__(system)
        self.port = port

        self.app = Flask(__name__)
        self.socket = SocketIO(self.app, cors_allowed_origins="*")

        @self.app.route("/")
        def index(self):
            return "index.html"

        @self.socket.on("connect")
        def connect():
            print("connected!")

        @self.socket.on("add_derived_signal")
        def add_derived_signal(response):
            # arg_dict = {arg["name"]: arg["value"] for arg in response["args"]}
            # self.system.add_derived_signal(name_to_signal[response["sig_name"]](**arg_dict))
            print(response)

        print(f"opened server on http://localhost:{self.port}")

    def update(self, data: DataBuffer):
        data_dict = {}
        for key, value in data.items():
            value = np.array(value)

            if np.iscomplexobj(value):
                value = np.log10(np.maximum(np.abs(value), 1e-10))

            if value.ndim < 2:
                value = value[None]

            data_dict[key] = value.tolist()

        self.socket.emit("data", data_dict, broadcast=True)

    def run(self):
        self.app.run(port=self.port)
