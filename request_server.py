import argparse

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

from signal_processing.system import SignalSystem
from signal_processing.data_sources import ManualTimerDataSource, MouseDataSource


app = Flask(__name__)
socket = SocketIO(app)

@app.route("/")
def plot():
    return render_template("plot.html")

SIG_NAMES = []

@socket.on("add_signal", namespace="/data")
def handle_add_signal(sig_name):
    if sig_name not in SIG_NAMES:
        SIG_NAMES.append(sig_name)

@socket.on("remove_signal", namespace="/data")
def handle_remove_signal(sig_name):
    if sig_name in SIG_NAMES:
        SIG_NAMES.remove(sig_name)

@socket.on("request", namespace="/data")
def handle_request(): # arg to control read/view?, ...
    data = system.read(as_dataframe=False)
    data = {k: v.tolist() for k, v in data.items() if k in SIG_NAMES}

    emit("response", data)


def main(host, port, sampling_rate, fetch_x_sec, debug):
    source = ManualTimerDataSource(sampling_rate=sampling_rate, secondary_sources=[MouseDataSource()])
    global system
    system = SignalSystem(source, derived=[], buffer_len=int(sampling_rate * fetch_x_sec))
    
    with system: # could handle system.start() and system.stop() with websocket events
        socket.run(app, host=host, port=port, debug=debug)

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--host", type=str, default="127.0.0.1")
    argparser.add_argument("--port", type=int, default=5000)
    argparser.add_argument("--sampling-rate", type=int, default=100)
    argparser.add_argument("--fetch-x-sec", type=int, default=2)
    argparser.add_argument("--debug", action="store_true", default=False)
    args = argparser.parse_args()

    main(args.host, args.port, args.sampling_rate, args.fetch_x_sec, args.debug)
