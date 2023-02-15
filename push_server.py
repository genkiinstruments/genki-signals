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
from flask import Flask, render_template
from flask_socketio import SocketIO

import signal_processing.signals as s  # noqa: E402
from signal_processing.data_sources import (  # noqa: E402
    ManualTimerDataSource,
    MouseDataSource,
    RandomDataSource,
    MouseDataSource,
    WaveDataSource,
)  # noqa: E402
from signal_processing.system import SignalSystem  # noqa: E402

eventlet.monkey_patch()
app = Flask(__name__)
socketio = SocketIO(app)

SAMPLING_RATE = 100
GUI_UPDATE_RATE = 60
BLE_ADDRESS = "905EC87A-AD3A-3CE7-21AE-9C97B8CA54E1"

def generate_data():
    # source = ManualTimerDataSource(
    #     SAMPLING_RATE, secondary_sources=[RandomDataSource(), MouseDataSource()]
    # )
    # source = WaveDataSource(
    #     ble_address=BLE_ADDRESS, secondary_sources=[RandomDataSource(), MouseDataSource()]
    # )
    # system = SignalSystem(source, derived=[s.SamplingRate()])
    global system
    with system:
        while True:
            data = system.read(as_dataframe=False)
            data_points = [dict(zip(data, [list(j) for j in i])) for i in zip(*data.values())]
            socketio.emit("data", data_points, broadcast=True, namespace='/data')
            socketio.sleep(1 / GUI_UPDATE_RATE)


@app.route("/")
def index():
    return render_template("plot.html")


@socketio.on("connect", namespace="/data")
def handle_connect():
    print("client connected")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3000)
    parser.add_argument("--debug", action="store_true", default=False)
    args = parser.parse_args()

    source = WaveDataSource(
        ble_address=BLE_ADDRESS, secondary_sources=[RandomDataSource(), MouseDataSource()]
    )
    global system
    system = SignalSystem(source, derived=[s.SamplingRate()])

    socketio.start_background_task(generate_data)
    socketio.run(app, host=args.host, port=args.port, debug=args.debug)
