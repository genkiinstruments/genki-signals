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
    def __init__(self, system: SignalSystem):
        super().__init__(system)
        self.update_callbacks = {}

    def register_update_callback(self, id, update_fn):
        self.update_callbacks[id] = update_fn

    def unregister_update_callback(self, id):
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
            x_access: tuple[str, int],
            y_access: tuple[str, int] | tuple[str, list[int]],
            n_visible_points: int
        ):
        """
        A line plot of a signal
        Args:
            x_access: The key index pair of the x-axis data, should map to a 1D signal
            y_access: The key index pair of the y-axis data (or list of indices), -1 for all
            n_visible_points: The number of points to show on the plot
        """
        super().__init__()

        self.x_key, self.x_idx = x_access
        self.y_key, self.y_idx = y_access

        self.buffer = DataBuffer(max_buffer_size=n_visible_points)

        x_scale = bq.LinearScale()
        y_scale = bq.LinearScale()
        self.x_axis = bq.Axis(scale=x_scale, label=self.x_accessor.name)
        self.y_axis = bq.Axis(scale=y_scale, orientation="vertical", label=self.y_accessor.name)
        self.line = bq.Lines(x=[], y=[], scales={"x": x_scale, "y": y_scale})

        self.widget = bq.Figure(marks=[self.line], axes=[self.x_axis, self.y_axis])

    def update(self, data: DataBuffer):
        self.buffer.extend({
            "x_key": data[self.x_key][self.x_idx],
            "y_key": data[self.y_key] if self.y_idx == -1 else data[self.y_key][self.y_idx]
        })
  
        x_data = self.buffer["x_key"]
        y_data = self.buffer["y_key"]

        with self.line.hold_sync():
            self.line.x = x_data
            self.line.y = y_data