"""
A simple webserver to demonstrate SocketIO workflow. To run install:

  $ pip install flask flask-socketio simple-websocket

and run this file. It uses the signal system to generate random data and stream
via websocket to browser. The sampling rate of the system and the rate at
which data is streamed can be set independently using the constants SAMPLING_RATE
and GUI_UPDATE_RATE.
"""
from flask import Flask, render_template
from flask_socketio import SocketIO

from threading import Lock
import sys
from pathlib import Path

from signal_processing.data_sources import (
    ManualTimerDataSource,
    RandomDataSource,
)  # noqa: E402
from signal_processing.system import SignalSystem  # noqa: E402
import signal_processing.signals as s  # noqa: E402

app = Flask(__name__)
socketio = SocketIO(app)

thread_lock = Lock()
data_thread = None

SAMPLING_RATE = 100
GUI_UPDATE_RATE = 100


def generate_data():
    source = ManualTimerDataSource(
        SAMPLING_RATE, secondary_sources=[RandomDataSource()]
    )
    system = SignalSystem(source, derived=[s.SamplingRate()])
    with system:
        while True:
            data = system.read(as_dataframe=False)
            for key, val in data.items():
                data[key] = val.tolist()
            socketio.emit("data", data, broadcast=True)
            socketio.sleep(1 / GUI_UPDATE_RATE)


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("connect")
def handle_connect():
    print("client connected")
    global data_thread
    with thread_lock:
        if data_thread is None:
            data_thread = socketio.start_background_task(generate_data)


if __name__ == "__main__":
    socketio.run(app, debug=True)
