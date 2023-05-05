from __future__ import annotations

from abc import ABC, abstractmethod

import cv2
import bqplot as bq
from ipywidgets import Image

from genki_signals.buffers import DataBuffer
from genki_signals.signal_system import SignalSystem
from genki_signals.signal_frontends.base import FrontendBase

class PlottableWidget(ABC):
    def __init__(self):
        self.widget = None

    @abstractmethod
    def update(self, data: DataBuffer):
        pass

class WidgetFrontend(FrontendBase):
    def __init__(self, system: SignalSystem, widgets: list[PlottableWidget] = None):
        super().__init__(system)

        self.update_callbacks = {id(widget): widget.update for widget in widgets or []}

    def register_update_callback(self, id, update_fn):
        self.update_callbacks[id] = update_fn

    def deregister_update_callback(self, id):
        self.update_callbacks.pop(id)

    def update(self, data: DataBuffer):
        for update_fn in self.update_callbacks.values():
            update_fn(data)


class Video(PlottableWidget):
    def __init__(self, video_key: str):
        super().__init__()

        self.video_key = video_key
        self.widget = Image(format="jpeg")
    
    def update(self, data: DataBuffer):
        value = data[self.video_key][..., -1].transpose(2, 1, 0)
        _, jpeg_image = cv2.imencode(".jpeg", value)
        self.widget.value = jpeg_image.tobytes()

class Line(PlottableWidget):
    def __init__(
            self,
            x_access: str | tuple[str, int],
            y_access: str | tuple[str, int] | tuple[str, list[int]],
            n_visible_points: int = 200
        ):
        """
        A line plot of a signal
        Args:
            x_access: The key of a 1D signal or key index pair of 2D signal which should map to a 1D signal,
                      defines how to access the the x-axis data
            y_access: The key of a signal or key index/indices pair of a 2D signal, defines how to access
                      the y-axis data
            n_visible_points: The number of points to show on the plot
        """
        super().__init__()

        if isinstance(x_access, str):
            x_access = (x_access, None)
        if isinstance(y_access, str):
            y_access = (y_access, None)

        self.x_key, self.x_idx = x_access
        self.y_key, self.y_idx = y_access

        self.buffer = DataBuffer(maxlen=n_visible_points)

        x_scale = bq.LinearScale()
        y_scale = bq.LinearScale()
        self.x_axis = bq.Axis(scale=x_scale, label=f"{self.x_key}_{self.x_idx}" if self.x_idx != None else self.x_key)
        self.y_axis = bq.Axis(scale=y_scale, orientation="vertical", label=f"{self.y_key}_{self.y_idx}" if self.y_idx != None else self.y_key)
        self.line = bq.Lines(x=[], y=[], scales={"x": x_scale, "y": y_scale})

        self.widget = bq.Figure(marks=[self.line], axes=[self.x_axis, self.y_axis])

    def update(self, data: DataBuffer):
        self.buffer.extend({
            "x_key": data[self.x_key] if self.x_idx == None else data[self.x_key][self.x_idx],
            "y_key": data[self.y_key] if self.y_idx in [-1, None] else data[self.y_key][self.y_idx]
        })
  
        x_data = self.buffer["x_key"]
        y_data = self.buffer["y_key"]

        with self.line.hold_sync():
            self.line.x = x_data
            self.line.y = y_data