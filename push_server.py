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
    Sampler
)
from genki_signals.system import System  # noqa: E402

eventlet.monkey_patch()
app = Flask(__name__)
CORS(app, origins='http://localhost:5173/*')
socketio = SocketIO(app, cors_allowed_origins="*")

SAMPLING_RATE = 100
GUI_UPDATE_RATE = 50


def generate_data(ble_address=None):
    if ble_address is not None:
        source = WaveDataSource(ble_address)
    else:
        source = Sampler({
            "random": RandomNoise(),
            "mouse_position": MouseDataSource()
        }, SAMPLING_RATE, timestamp_key="timestamp_us")
        
    with System(source, [s.SampleRate(input_name="timestamp_us")]) as system:
        while True:
            data = system.read()
            data_dict = {}
            for key in data:
                if data[key].ndim == 1:
                    data_dict[key] = data[key][:, None].T.tolist()
                else:
                    data_dict[key] = data[key].T.tolist()
            socketio.emit("data", data_dict, broadcast=True)
            socketio.sleep(1 / GUI_UPDATE_RATE)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--ble-address", type=str, default=None)
    args = parser.parse_args()

    socketio.start_background_task(generate_data, args.ble_address)
    socketio.run(app, host=args.host, port=args.port, debug=args.debug)
