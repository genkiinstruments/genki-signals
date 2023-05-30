from __future__ import annotations

import datetime
import logging
import numpy as np

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui
from PyQt5 import QtCore, QtWidgets

from genki_signals.system import System
from genki_signals.buffers import DataBuffer
from genki_signals.frontends.base import FrontendBase
from genki_signals.frontends.qt_plots import Plottable
logger = logging.getLogger(__name__)


def position_iterator(num_cols):
    row = 0
    while True:
        for col in range(num_cols):
            yield row, col
        row += 1 


class QtDashboard(FrontendBase):
    def __init__(self, system: System, plots: list[Plottable], n_cols: int = 3):
        super().__init__(system)

        self.system = system
        self.uninitialized_plots = plots

        self.app = QtWidgets.QApplication([])
        pg.setConfigOptions(antialias=True)
        self.main_widget = QtWidgets.QWidget()
        self.main_widget.setStyleSheet("background-color: black; color: white;")
        self.main_layout = QtWidgets.QGridLayout()
        self.main_widget.setLayout(self.main_layout)

        self.position_iter = position_iterator(n_cols)

        top = QtWidgets.QWidget()
        top_layout = QtWidgets.QGridLayout()
        top_layout.setAlignment(QtCore.Qt.AlignCenter)

        self.paused = False
        self.pause_icon = self.main_widget.style().standardIcon(QtWidgets.QStyle.SP_MediaPause)
        self.play_icon = self.main_widget.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay)
        self.pause_button = QtWidgets.QPushButton(self.pause_icon, "")
        top_layout.addWidget(self.pause_button)
        self.pause_button.clicked.connect(self.on_pause)

        self.recording = False
        self.rec_button = QtWidgets.QPushButton("Record...")
        top_layout.addWidget(self.rec_button)
        self.rec_button.clicked.connect(self.on_record)

        top.setLayout(top_layout)
        self.main_layout.addWidget(top, *next(self.position_iter))

        next(self.position_iter)

        self.text_font = QtGui.QFont()
        self.text_font.setPixelSize(50)

    def add_plot(self, plot: Plottable):
        self.main_layout.addWidget(plot.widget, *next(self.position_iter))
        self.plots.append(plot)

    def remove_graph(self, plot: Plottable):
        if plot in self.plots:
            plot.widget.setParent(None)
            self.plots.remove(plot)

    def on_pause(self):
        if self.paused:
            self.paused = False
            self.pause_button.setIcon(self.pause_icon)
        else:
            self.paused = True
            self.pause_button.setIcon(self.play_icon)

    def on_record(self):
        pass

    def update(self, data: DataBuffer):
        if len(data) == 0:
            return
        
        if not hasattr(self, "plots"):
            self.plots = []
            for plot in self.uninitialized_plots:
                plot.init_when_ready(data)
                self.add_plot(plot)
            self.uninitialized_plots = []
        
        if self.paused:
            return

        for plot in self.plots:
            plot.update(data)

        if self.recording:
            recording_time = datetime.datetime.now() - self.started_recording
            self.rec_button.setText(f"Stop recording (recording for {str(recording_time).split('.')[0]}).")

    def run(self):
        self.main_widget.show()
        self.app.exec_()
        # from IPython.lib.guisupport import start_event_loop_qt4
        # start_event_loop_qt4(self.app)



def main(
    sample_rate: int,
    update_rate: int,
):  
    source = Sampler({"mouse": MouseSource()}, sample_rate=sample_rate)
    system = System(source, [], update_rate=update_rate)

    plots = [p.Line("timestamp", "mouse")]
    dashboard = QtDashboard(
        system=system,
        # plots = [],
        plots=plots
    )

    buffer = DataBuffer()
    buffer.extend({
        "timestamp": np.zeros(10),
        "mouse": np.zeros((2,10)),
    })
    dashboard.update(buffer)

    with system:
        timer = QtCore.QTimer()
        timer.start(update_rate)
        dashboard.run()


if __name__ == "__main__":
    import argparse
    
    import genki_signals.frontends.qt_plots as p # noqa: E402
    from genki_signals.sources import MouseSource, Sampler # noqa: E402
    from genki_signals.system import System  # noqa: E402

    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-rate", type=int, default=100)
    parser.add_argument("--update-rate", type=int, default=50)
    args = parser.parse_args()

    main(
        args.sample_rate,
        args.update_rate,
    )

