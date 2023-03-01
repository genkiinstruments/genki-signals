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

import signal_processing.signals as s  # noqa: E402
from signal_processing.data_sources import (  # noqa: E402
    ManualTimerDataSource,
    MouseDataSource,
    RandomDataSource,
    WaveDataSource
)
from signal_processing.system import SignalSystem  # noqa: E402

eventlet.monkey_patch()
app = Flask(__name__)
CORS(app, origins='http://localhost:5173/*')
socketio = SocketIO(app, cors_allowed_origins="*") #, cors_allowed_origins=["http://localhost:5173/"]) # TODO: remove cors_allowed_origins

SAMPLING_RATE = 100
GUI_UPDATE_RATE = 50


def generate_data(ble_address=None):
    ds = [RandomDataSource(), MouseDataSource()]
    if ble_address is not None:
        source = WaveDataSource(ble_address, secondary_sources=ds)
    else:
        source = ManualTimerDataSource(SAMPLING_RATE, secondary_sources=ds)
        
    system = SignalSystem(source, derived=[s.SamplingRate()])
    with system:
        while True:
            data = system.read(as_dataframe=False)
        
            for key in data:
                data[key] = data[key].T.tolist() # NOTE: easier to work with in JS
        
            socketio.emit("data", data, broadcast=True)
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
