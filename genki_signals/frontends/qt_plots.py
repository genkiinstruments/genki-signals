from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Literal

import numpy as np
from more_itertools import zip_equal

import pyqtgraph as pg
from PyQt5 import QtCore
import pyqtgraph.opengl as gl
from pyqtgraph.Qt import QtGui
from genki_signals.buffers import DataBuffer

from genki_signals.frontends.opengl_cube import cube_mesh  # noqa: E402


logger = logging.getLogger(__name__)

CONFIG = {
    "legend_size": 15,
    "pen_colors": ["r", "g", "c", "b", "m"],  # Do we need more colors?
}


class Plottable(ABC):
    def __init__(self):
        self.widget = None
        self.layout = None

    @abstractmethod
    def init_when_ready(self, data: DataBuffer):
        pass

    @abstractmethod
    def update(self, data):
        pass

    def set_visible(self, visible):
        self.widget.setVisible(visible)


class Line(Plottable):
    def __init__(
        self,
        x_access: str | tuple[str, int],
        y_access: str | tuple[str, int] | tuple[str, list[int]],
        x_scale: Literal["linear", "log"] = "linear",
        y_scale: Literal["linear", "log"] = "linear",
        x_range: tuple[float, float] = (None, None),
        y_range: tuple[float, float] = (None, None),    
        n_visible_points: int = 200,
    ):
        super().__init__()

        if isinstance(x_access, str):
            x_access = (x_access, None)
        if isinstance(y_access, str):
            y_access = (y_access, None)

        self.x_key, self.x_idx = x_access
        self.y_key, self.y_idx = y_access
        self.y_idx = self.y_idx if isinstance(self.y_idx, list) else [self.y_idx]

        self.x_scale = x_scale
        self.y_scale = y_scale
        self.x_range = x_range
        self.y_range = y_range

        self.buffer = DataBuffer(n_visible_points)

    def init_when_ready(self, data: DataBuffer):
        """Creates a plot for each y_idx and colors accordingly."""
        self.widget = QtGui.QWidget()
        self.layout = QtGui.QVBoxLayout()
        self.widget.setLayout(self.layout)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.addLegend(labelTextSize=f'{CONFIG["legend_size"]}pt')
        self.layout.addWidget(self.plot_widget)
        
        if self.y_idx is None:
            self.y_idx = list(range(data[self.y_key].shape[0]))

        self.plots = [self.plot_widget.plot(
            name = f"{self.y_key}_{idx}",
            pen = CONFIG["pen_colors"][i],
        ) for i, idx in enumerate(self.y_idx)]

        # for plot in self.plots:
            # plot.setLogMode(x=self.x_scale == "log", y=self.y_scale == "log")
            # plot.vb.setLimits(xMin=self.x_range[0], xMax=self.x_range[1], yMin=self.y_range[0], yMax=self.y_range[1])

    def update(self, data):        
        self.buffer.extend(
            {
                "x_key": data[self.x_key] if self.x_idx is None else data[self.x_key][self.x_idx],
                "y_key": data[self.y_key] if self.y_idx is None else data[self.y_key],
            }
        )
        x = self.buffer["x_key"]
        for i, plot in enumerate(self.plots):
            y = self.buffer["y_key"][i]
            plot.setData(x, y)


# class Histogram(Plottable):
#     """
#     Graph element for plotting histograms.
#     If column_names is not specified, signal_names will be used.
#     """

#     def __init__(self, *args, column_names: tuple[str] = None, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.column_names = column_names or self.signal_names

#     def _init_plots(self, data):
#         """Checks if naming convention is followed and initializes the histogram."""
#         validate_data(data, self.processed_names)

#         signals = list(
#             signal_iterator(data, self.processed_names)
#         )  # Iterator depletes when looping over it, we store it in a list for simplicity
#         assert len(self.column_names) == len(
#             list(signals)
#         ), "Must have the same number of signal names and column names"

#         for i, (sig_name, sig_idx) in enumerate(signals):
#             bar = pg.BarGraphItem(
#                 x=[i],
#                 height=[0],
#                 width=self.cfg["bar_width"],
#                 brush=self.cfg["pen_colors"][i],
#                 name=f"{self.column_names[i]}",
#             )
#             self.plot_widget.addItem(bar)
#             self.bars[(sig_name, sig_idx)] = bar

#     def setup(self, cfg):
#         super().setup(cfg)

#         self.bars = {}
#         self.plot_widget = pg.PlotWidget()
#         self.plot_widget.addLegend(labelTextSize=f'{cfg["legend_size"]}pt')
#         self.layout.addWidget(self.plot_widget)

#     def update(self, data):
#         if not hasattr(self, "bars"):
#             logger.warning("Graph element has no attribute 'bars', did you call setup()?")
#             return

#         if not self.bars:
#             self._init_plots(data)

#         for (name, idx), bar in self.bars.items():
#             bar.setOpts(height=fetch_data(data, name, idx)[-1])  # fetch last value


# class Trace(Plottable):
#     """
#     Graph element for plotting 2D or 3D traces.
#     In the case of 3D traces, the third dimension is used for color.
#     """

#     def __init__(self, sig_x: str, sig_y: str, sig_z: str = None, num_points_visible: int = 200, **kwargs):
#         kwargs.pop("signal_names", None)
#         self.signal_names = (sig_x, sig_y, sig_z) if sig_z else (sig_x, sig_y)
#         self.num_points_visible = num_points_visible

#         if len(self.signal_names) > 2:
#             raise NotImplementedError("3D traces are not implemented yet")

#         super().__init__(self.signal_names, **kwargs)

#     def _init_trace(self, data):
#         """Checks if naming convention is followed and initializes the trace."""
#         validate_data(data, self.processed_names)

#         self.trace = pg.PlotCurveItem(name="2D trace")
#         self.plot_widget.addItem(self.trace)

#     def setup(self, cfg):
#         super().setup(cfg)

#         self.trace = None
#         self.plot_widget = pg.PlotWidget()
#         self.plot_widget.addLegend(labelTextSize=f'{cfg["legend_size"]}pt')
#         self.layout.addWidget(self.plot_widget)

#     def update(self, data):
#         if not hasattr(self, "trace"):
#             logger.warning("Graph element has no attribute 'trace', did you call setup()?")
#             return

#         if not self.trace:
#             self._init_trace(data)

#         x_name, x_idx = self.processed_names[0]
#         y_name, y_idx = self.processed_names[1]
#         x_idx = x_idx or 0
#         y_idx = y_idx or 0
#         x = fetch_data(data, x_name, x_idx)
#         y = fetch_data(data, y_name, y_idx)
#         self.trace.setData(
#             x, -y
#         )  # NOTE(bjarni): This is overfitted to mouse data since (0,0) is in the top left corner


# class FormatText(Plottable):
#     """
#     Graph element for displaying formatted text.
#     E.g.
#         FormatText("sampling_rate", "Current sampling rate: {:.2f} Hz")

#     will display the text "Current sampling rate: 100.00 Hz" if the signal "sampling_rate" has the value 100.
#     """

#     # TODO(bjarni): Add a parameter to specify text location (top, bottom, left, right, center)
#     def __init__(self, *args, format_strs: str | tuple[str], **kwargs):
#         super().__init__(*args, **kwargs)
#         self.format_strs = format_strs if isinstance(format_strs, (tuple, list)) else (format_strs,)

#         assert len(self.processed_names) == len(
#             self.format_strs
#         ), "Must have same number of signal names and format strings"

#     def _init_text(self, data):
#         """Checks if naming convention is followed and initializes the text."""
#         validate_data(data, self.processed_names)

#         for sig_name, sig_idx in signal_iterator(data, self.processed_names):
#             text = QtGui.QLabel()
#             text.setAlignment(QtCore.Qt.AlignCenter)  # TODO(bjarni): Add parameter to specify alignment
#             self.layout.addWidget(text)
#             self.texts[(sig_name, sig_idx)] = text

#     def setup(self, cfg):
#         super().setup(cfg)
#         self.texts = {}

#     def update(self, data):
#         if not hasattr(self, "texts"):
#             logger.warning("Graph element has no attribute 'texts', did you call setup()?")
#             return

#         if not self.texts:
#             self._init_text(data)

#         for (sig_name, sig_idx), format_str in zip_equal(self.texts, self.format_strs):
#             # NOTE(bjarni): Only the first index in processed is used if all are specified (i.e. [] is 0)
#             # TODO(bjarni): How to properly handle this case or multiple indices?
#             sig_idx = 0 if sig_idx is None else sig_idx  # if no index is specified, use the first index
#             value = fetch_data(data, sig_name, sig_idx)[-1]
#             self.texts[(sig_name, sig_idx)].setText(format_str.format(value))


# class MapToText(Plottable):
#     """
#     Graph element for displaying text where the text is determined by a value map.
#     E.g.
#         ToText("pressing_a", {0: "Not pressing a", 1: "Pressing a"})

#     will display the text "Pressing a" if the signal "pressing_a" has the value 1.
#     """

#     def __init__(self, *args, value_maps: dict | tuple[dict], **kwargs):
#         super().__init__(*args, **kwargs)
#         self.value_maps = value_maps if isinstance(value_maps, (tuple, list)) else (value_maps,)

#         assert len(self.processed_names) == len(self.value_maps), "Must have same number of signal names and value maps"

#     def _init_text(self, data):
#         """Checks if naming convention is followed and initializes the text."""
#         validate_data(data, self.processed_names)

#         for sig_name, sig_idx in signal_iterator(data, self.processed_names):
#             text = QtGui.QLabel()
#             text.setAlignment(QtCore.Qt.AlignCenter)
#             self.layout.addWidget(text)
#             self.texts[(sig_name, sig_idx)] = text

#     def setup(self, cfg):
#         super().setup(cfg)
#         self.texts = {}

#     def update(self, data):
#         if not hasattr(self, "texts"):
#             logger.warning("Graph element has no attribute 'texts', did you call setup()?")
#             return

#         if not self.texts:
#             self._init_text(data)

#         for (sig_name, sig_idx), value_map in zip(self.texts, self.value_maps):
#             sig_idx = 0 if sig_idx is None else sig_idx  # if no index is specified, use the first index
#             value = fetch_data(data, sig_name, sig_idx)[-1]
#             assert value in value_map, f"{value=} not in {value_map=}"
#             value = value_map[value]
#             self.texts[(sig_name, sig_idx)].setText(str(value))


# class Video(Plottable):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         pg.setConfigOption("imageAxisOrder", "row-major")  # important for performance since c is row-major

#         assert len(self.processed_names) == 1, "Video graph element can only display one signal"

#     def setup(self, cfg):
#         super().setup(cfg)

#         self.plot_widget = pg.PlotWidget()
#         self.plot_widget.addLegend(labelTextSize=f'{cfg["legend_size"]}pt')
#         self.plot_widget.hideAxis("left")
#         self.plot_widget.hideAxis("bottom")
#         self.layout.addWidget(self.plot_widget)

#         self.frame = pg.ImageItem()
#         self.frame.scaleToImage = True

#         self.plot_widget.addItem(self.frame)

#     def update(self, data):
#         image = data[self.signal_names[0]]
#         image = np.rot90(image[-1], 2)
#         self.frame.setImage(image)


# class Spectrogram(Plottable):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         pg.setConfigOption("imageAxisOrder", "row-major")  # important for performance since c is row-major

#         assert len(self.processed_names) == 1, "Spectrogram graph element can only display one signal"

#     def setup(self, cfg):
#         super().setup(cfg)

#         self.spectro_widget = pg.PlotWidget()
#         self.spectro_widget.addLegend(labelTextSize=f'{cfg["legend_size"]}pt')
#         self.img = pg.ImageItem()
#         self.layout.addWidget(self.spectro_widget)
#         self.spectro_widget.addItem(self.img)
#         self.hist = pg.HistogramLUTItem()
#         self.hist.setImageItem(self.img)
#         self.hist.setLevels(4e-06, 0.042)
#         self.hist.gradient.restoreState(
#             {
#                 "mode": "rgb",
#                 "ticks": [
#                     (0.5, (153, 0, 76, 255)),
#                     (0.8, (255, 51, 51, 240)),
#                     (1.0, (255, 255, 102, 220)),
#                 ],
#             }
#         )

#     def update(self, data):
#         image = data[self.signal_names[0]]
#         self.img.setImage(image.T)


# class OrientationCube(Plottable):
#     """
#     Graph element for displaying a 3D cube using OpenGL.
#     """

#     def setup(self, cfg):
#         super().setup(cfg)

#         gl_view = gl.GLViewWidget()
#         gl_view.setFixedHeight(200)

#         self.cube = cube_mesh()
#         gl_view.addItem(self.cube)
#         [gl_view.addItem(gl.GLAxisItem()) for _ in ["x", "y", "z"]]

#         # `azimuth=180` ensures that when the ring is oriented "normally" the cube will be oriented the same
#         gl_view.setCameraPosition(azimuth=180)
#         self.layout.addWidget(gl_view)

#     def update(self, data):
#         self.cube.resetTransform()

#         data = [
#             fetch_data(data, sig_name, sig_idx)[-1] for sig_name, sig_idx in signal_iterator(data, self.processed_names)
#         ]
#         assert len(data) == 4, "OrientationCube graph element expects quaternion rotation signal"

#         self.cube.rotate(*data)