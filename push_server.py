"""
A simple webserver to demonstrate SocketIO workflow. To run install:

  $ pip install flask flask-socketio eventlet

and run this file. It uses the signal system to generate random data and stream
via websocket to browser. The sampling rate of the system and the rate at
which data is streamed can be set independently using the constants SAMPLING_RATE
and GUI_UPDATE_RATE.
"""
import argparse

import eventlet
from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS

import genki_signals.signals as s  # noqa: E402
from genki_signals.data_sources import (  # noqa: E402
    WaveDataSource
)
from genki_signals.data_sources import (
    MouseDataSource,
    RandomNoise,
    MicDataSource,
    Sampler
)
from genki_signals.system import System  # noqa: E402
from genki_signals.models.letter_detection_model import SimpleGruModel  # noqa: E402

import numpy as np

eventlet.monkey_patch()
app = Flask(__name__)
CORS(app, origins='http://localhost:5173/*')
# CORS(app, resources={r"/*":{"origins":"*"}})
# socketio = SocketIO(app, cors_allowed_origins="*", engineio_logger=True, logger=True)
socketio = SocketIO(app, cors_allowed_origins="*")

SAMPLING_RATE = 100
GUI_UPDATE_RATE = 50
DATA_SOURCE = 'Mic'
# DATA_SOURCE = 'Sampler'

from inspect import signature, getmembers, isclass

derived_signals = {}
name_to_signal = {}
for sig_name, sig in getmembers(s,isclass):
    name_to_signal[sig_name] = sig
    derived_signals[sig_name] = {}
    for arg in signature(sig, follow_wrapped=True).parameters.values():
        derived_signals[sig_name][arg.name] = {
            "type": str(arg.annotation),
            "default": arg.default if arg.default is not arg.empty else "",
        }

def generate_data(ble_address=None):
    if ble_address is not None:
        source = WaveDataSource(ble_address)
    if DATA_SOURCE == 'Mic':
        source = MicDataSource()
        print(source.sample_rate)
    elif DATA_SOURCE == 'Sampler':
        source = Sampler({
            "random": RandomNoise(),
            "mouse_position": MouseDataSource()
        }, SAMPLING_RATE, timestamp_key="timestamp")

    with System(source) as system:
        @socketio.on("derived_signal")
        def add_derived_signal(response):
            arg_dict = {arg["name"]:arg["value"] for arg in response["args"]}
            system.add_derived_signal(name_to_signal[response["sig_name"]](**arg_dict))

        while True:
            data = system.read()
            data_dict = {}
            for key in data:
                if data[key].ndim == 1:
                    data_dict[key] = data[key][None, :].tolist()
                else:
                    data_dict[key] = data[key].tolist()
            if("fourier" in data):
                data_dict["fourier"] = np.log10(np.abs(data_dict["fourier"]) + 1).tolist()
            socketio.emit("data", data_dict, broadcast=True)
            socketio.sleep(1 / GUI_UPDATE_RATE)


@socketio.on('connect')
def send_derived_signals(response):
    socketio.emit("derived_signals", derived_signals)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--ble-address", type=str, default=None)
    args = parser.parse_args()

    socketio.start_background_task(generate_data, args.ble_address)
    socketio.run(app, host=args.host, port=args.port, debug=args.debug)
