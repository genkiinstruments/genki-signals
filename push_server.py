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
)
from signal_processing.system import SignalSystem  # noqa: E402

eventlet.monkey_patch()
app = Flask(__name__)
CORS(app, origins='http://localhost:5173/*')
socketio = SocketIO(app, cors_allowed_origins="*") #, cors_allowed_origins=["http://localhost:5173/"]) # TODO: remove cors_allowed_origins

SAMPLING_RATE = 1000
GUI_UPDATE_RATE = 500


def generate_data():
    source = ManualTimerDataSource(
        SAMPLING_RATE, secondary_sources=[RandomDataSource(), MouseDataSource()]
    )
    system = SignalSystem(source, derived=[s.SamplingRate()])
    with system:
        while True:
            data = system.read(as_dataframe=False)
            # data_points = [dict(row) for _, row in data.iterrows()]
            data_points = [dict(zip(data, [list(v) for v in vs])) for vs in zip(*data.values())]
            socketio.emit("data", data_points, broadcast=True)
            socketio.sleep(1 / GUI_UPDATE_RATE)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()

    socketio.start_background_task(generate_data)
    socketio.run(app, host=args.host, port=args.port, debug=True)
