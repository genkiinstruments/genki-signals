from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import Literal

import cv2
import bqplot as bq
import ipywidgets
from ipywidgets import Image
from IPython.display import display

from genki_signals.buffers import DataBuffer
from genki_signals.system import System
from genki_signals.frontends.base import FrontendBase


class WidgetDashboard:
    """
    A simple dashboard for displaying multiple widgets in a grid.
    """
    def __init__(self, widgets: list[PlottableWidget]):
        self.widgets = widgets

    def _ipython_display_(self):
        n = math.ceil(math.sqrt(len(self.widgets)))
        rows = []
        for i in range(n):
            cols = []
            for j in range(n):
                try:
                    cols.append(self.widgets[i * n + j].widget)
                except IndexError:
                    pass
            rows.append(ipywidgets.HBox(cols))
        return display(ipywidgets.VBox(rows))


class PlottableWidget(FrontendBase):
    """
    A base class for jupyter frontends.
    """
    def __init__(self, system: System):
        super().__init__(system)

        self.widget = None

    @abstractmethod
    def update(self, data: DataBuffer):
        pass

    def _ipython_display_(self):
        return display(self.widget)


class Video(PlottableWidget):
    def __init__(self, system: System, video_key: str):
        super().__init__(system)

        self.video_key = video_key
        self.widget = Image(format="jpeg")

    def update(self, data: DataBuffer):
        transpose = (2, 1, 0) if data[self.video_key].ndim == 4 else (1, 0)  # rgb or grayscale
        value = data[self.video_key][..., -1].transpose(transpose)
        _, jpeg_image = cv2.imencode(".jpeg", value)
        self.widget.value = jpeg_image.tobytes()


class Line(PlottableWidget):
    """A line plot of a signal w.r.t. some 1D signal."""

    def __init__(
        self,
        system: System,
        x_access: str | tuple[str, int],
        y_access: str | tuple[str, int] | tuple[str, list[int]],
        x_scale: Literal["linear", "log"] = "linear",
        y_scale: Literal["linear", "log"] = "linear",
        x_range: tuple[float, float] = (None, None),
        y_range: tuple[float, float] = (None, None),
        n_visible_points: int = 200,
        flip_x: bool = False,
        flip_y: bool = False,
    ):
        """
        Args:
            x_access: The key of a 1D signal or key index pair of 2D signal which should map to a 1D signal,
                      defines how to access the the x-axis data
            y_access: The key of a signal or key index/indices pair of a 2D signal, defines how to access
                      the y-axis data
            x_scale:  The scale of the x-axis, either "linear" or "log"
            y_scale:  The scale of the y-axis, either "linear" or "log"
            x_range:  The range of the x-axis, defaults to the range of the data at any given time i.e. (min(x), max(x))
            y_range:  The range of the y-axis, defaults to the range of the data at any given time i.e. (min(y), max(y))
            n_visible_points: The number of points to show on the plot
        """
        super().__init__(system)

        if isinstance(x_access, str):
            x_access = (x_access, None)
        if isinstance(y_access, str):
            y_access = (y_access, None)

        x_range = {"min": x_range[0], "max": x_range[1]}
        y_range = {"min": y_range[0], "max": y_range[1]}

        self.buffer = DataBuffer(maxlen=n_visible_points)

        self.x_key, self.x_idx = x_access
        self.y_key, self.y_idx = y_access

        x_scale = bq.LinearScale(**x_range, reverse=flip_x) \
            if x_scale == "linear" \
            else bq.LogScale(**x_range, reverse=flip_x)
        y_scale = bq.LinearScale(**y_range, reverse=flip_y) \
            if y_scale == "linear" \
            else bq.LogScale(**y_range, reverse=flip_y)
        self.x_axis = bq.Axis(
            scale=x_scale, label=f"{self.x_key}_{self.x_idx}" if self.x_idx is not None else self.x_key
        )
        self.y_axis = bq.Axis(scale=y_scale, orientation="vertical", label=self.y_key)
        self.line = bq.Lines(x=[], y=[], scales={"x": x_scale, "y": y_scale})

        self.widget = bq.Figure(marks=[self.line], axes=[self.x_axis, self.y_axis])

    def update(self, data: DataBuffer):
        self.buffer.extend(
            {
                "x_key": data[self.x_key] if self.x_idx is None else data[self.x_key][self.x_idx],
                "y_key": data[self.y_key] if self.y_idx is None else data[self.y_key][self.y_idx],
            }
        )

        with self.line.hold_sync():
            self.line.x = self.buffer["x_key"]
            self.line.y = self.buffer["y_key"]


class Scatter(PlottableWidget):
    """A scatter plot of a 1D signal w.r.t. some 1D signal."""

    def __init__(
        self,
        system: System,
        x_access: str | tuple[str, int],
        y_access: str | tuple[str, int],
        x_scale: Literal["linear", "log"] = "linear",
        y_scale: Literal["linear", "log"] = "linear",
        x_range: tuple[float, float] = (None, None),
        y_range: tuple[float, float] = (None, None),
        n_visible_points: int = 200,
        flip_x: bool = False,
        flip_y: bool = False,
    ):
        """
        Args:
            x_access: The key of a 1D signal or key index pair of 2D signal which should map to a 1D signal,
                      defines how to access the the x-axis data
            y_access: The key of a 1D signal or key index pair of a 2D signal, which should map to a 1D signal,
                      defines how to access the y-axis data
            x_scale:  The scale of the x-axis, either "linear" or "log"
            y_scale:  The scale of the y-axis, either "linear" or "log"
            x_range:  The range of the x-axis, defaults to the range of the data at any given time i.e. (min(x), max(x))
            y_range:  The range of the y-axis, defaults to the range of the data at any given time i.e. (min(y), max(y))
            n_visible_points: The number of points to show on the plot
        """
        super().__init__(system)

        if isinstance(x_access, str):
            x_access = (x_access, None)
        if isinstance(y_access, str):
            y_access = (y_access, None)

        x_range = {"min": x_range[0], "max": x_range[1]}
        y_range = {"min": y_range[0], "max": y_range[1]}

        self.buffer = DataBuffer(maxlen=n_visible_points)

        self.x_key, self.x_idx = x_access
        self.y_key, self.y_idx = y_access

        x_scale = bq.LinearScale(**x_range, reverse=flip_x) if x_scale == "linear" else bq.LogScale(**x_range, reverse=flip_x)
        y_scale = bq.LinearScale(**y_range, reverse=flip_y) if y_scale == "linear" else bq.LogScale(**y_range, reverse=flip_y)
        self.x_axis = bq.Axis(scale=x_scale, label=self.x_key if self.x_idx is None else f"{self.x_key}_{self.x_idx}")
        self.y_axis = bq.Axis(
            scale=y_scale,
            orientation="vertical",
            label=self.y_key if self.y_idx is None else f"{self.y_key}_{self.y_idx}",
        )
        self.scatter = bq.Scatter(x=[], y=[], scales={"x": x_scale, "y": y_scale})

        self.widget = bq.Figure(marks=[self.scatter], axes=[self.x_axis, self.y_axis])

    def update(self, data: DataBuffer):
        self.buffer.extend(
            {
                "x_key": data[self.x_key] if self.x_idx is None else data[self.x_key][self.x_idx],
                "y_key": data[self.y_key] if self.y_idx is None else data[self.y_key][self.y_idx],
            }
        )
        with self.scatter.hold_sync():
            self.scatter.x = self.buffer["x_key"]
            self.scatter.y = self.buffer["y_key"]


class Histogram(PlottableWidget):
    """A histogram of values from a 1D signal over some lookback window."""

    def __init__(
        self,
        system: System,
        y_access: str | tuple[str, int],
        x_range: tuple[float, float] = (None, None),
        y_range: tuple[float, float] = (None, None),
        bin_count: int = 10,
        lookback_size: int = 100,
    ):
        """
        Args:
            y_access: The key of a 1D signal or key index pair of a 2D signal, should map to a 1D signal,
                      defines how to access the y-axis data
            y_range:  The range of the y-axis, defaults to the range of the data at any given time i.e. (min(y), max(y))
            bin_count: The number of bins in the histogram
            lookback_size: The number of points to look back when computing the histogram
        """
        super().__init__(system)

        if isinstance(y_access, str):
            y_access = (y_access, None)

        x_range = {"min": x_range[0], "max": x_range[1]}
        y_range = {"min": y_range[0], "max": y_range[1]}

        self.buffer = DataBuffer(maxlen=lookback_size)

        self.y_key, self.y_idx = y_access

        x_scale = bq.LinearScale(**x_range)
        y_scale = bq.LinearScale(**y_range)
        self.x_axis = bq.Axis(scale=x_scale, tick_format="0.2f")
        self.y_axis = bq.Axis(scale=y_scale, orientation="vertical", label=self.y_key)
        self.hist = bq.Hist(sample=[], bins=bin_count, scales={"sample": x_scale, "count": y_scale})
        self.widget = bq.Figure(marks=[self.hist], axes=[self.x_axis, self.y_axis], padding_y=0)

    def update(self, data: DataBuffer):
        self.buffer.extend({"y_key": data[self.y_key] if self.y_idx is None else data[self.y_key][self.y_idx]})
        with self.hist.hold_sync():
            self.hist.sample = self.buffer["y_key"]


class Bar(PlottableWidget):
    """A bar plot of values from a 2D signal, where each bar represents a different index of the signal."""

    def __init__(
        self,
        system: System,
        y_access: str | tuple[str, list[int]],
        x_names: list[str] = None,
        y_range: tuple[float, float] = (None, None),
    ):
        """
        Args:
            y_access: The key or key indices of a signal, defines how to access the y-axis data
            y_range:  The range of the y-axis, defaults to the range of the data at any given time i.e. (min(y), max(y))
            x_names:  The names of the bars on the x-axis
        """
        super().__init__(system)

        if isinstance(y_access, str):
            y_access = (y_access, None)

        y_range = {"min": y_range[0], "max": y_range[1]}

        self.y_key, self.y_idx = y_access
        self.x_names = x_names

        x_scale = bq.OrdinalScale()
        y_scale = bq.LinearScale(**y_range)
        self.x_axis = bq.Axis(scale=x_scale, label="indices")
        self.y_axis = bq.Axis(scale=y_scale, orientation="vertical", label=self.y_key)
        self.bars = bq.Bars(x=self.x_names or [], y=[], scales={"x": x_scale, "y": y_scale})
        self.widget = bq.Figure(marks=[self.bars], axes=[self.x_axis, self.y_axis])

    def update(self, data: DataBuffer):
        with self.bars.hold_sync():
            data = data[self.y_key] if self.y_idx is None else data[self.y_key][self.y_idx]
            if self.x_names is None:  # we cannot know how many bars there are beforehand
                self.bars.x = list(range(data.shape[0]))
            self.bars.y = data[..., -1]
