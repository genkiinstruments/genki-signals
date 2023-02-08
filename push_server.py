"""
A simple webserver to demonstrate SocketIO workflow. To run install:

  $ pip install flask flask-socketio eventlet

and run this file. It uses the signal system to generate random data and stream
via websocket to browser. The sampling rate of the system and the rate at
which data is streamed can be set independently using the constants SAMPLING_RATE
and GUI_UPDATE_RATE.
"""
import datetime
import sys
from pathlib import Path
from threading import Lock

import eventlet
import numpy as np
from flask import Flask, render_template
from flask_socketio import SocketIO

import signal_processing.signals as s  # noqa: E402
from signal_processing.data_sources import (  # noqa: E402
    ManualTimerDataSource,
    RandomDataSource,
)
from signal_processing.system import SignalSystem  # noqa: E402

eventlet.monkey_patch()
app = Flask(__name__)
socketio = SocketIO(app)

thread_lock = Lock()
data_thread = None

SAMPLING_RATE = 100
GUI_UPDATE_RATE = 50


def generate_data():
    source = ManualTimerDataSource(
        SAMPLING_RATE, secondary_sources=[RandomDataSource()]
    )
    # source = MicDataSource()
    system = SignalSystem(source, derived=[])
    print("called generate_data")
    with system:
        while True:
            data = system.read(as_dataframe=True)
            data_points = [dict(row) for _, row in data.iterrows()]
            socketio.emit("data", data_points, broadcast=True)
            socketio.sleep(1 / GUI_UPDATE_RATE)


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    socketio.start_background_task(generate_data)
    socketio.run(app, debug=True)
