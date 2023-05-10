import logging
import re
from abc import ABC, abstractmethod
from collections.abc import MutableMapping

import bqplot as bq
import cv2
import numpy as np
import pandas as pd
from ipywidgets import Image

logger = logging.getLogger(__name__)


def _slice(data, length, end=True):
    if end:
        return {k: v[..., -length:] for k, v in data.items()}
    else:
        return {k: v[..., :length] for k, v in data.items()}


class Buffer(ABC):
    """deque-like buffer for pandas dataframes and numpy arrays"""

    def __init__(self, maxlen, cols):
        if maxlen is not None and maxlen < 1:
            raise ValueError("Length of buffer has to be at least 1")
        self.maxlen = maxlen
        self.cols = cols
        self._data = self._empty()

    @abstractmethod
    def _init_cols_if_needed(self, data):
        # If columns are set at runtime
        pass

    @abstractmethod
    def _empty(self):
        """Returns an empty element"""
        pass

    @abstractmethod
    def _validate(self, data):
        """Validate the shape of the elements"""
        pass

    @abstractmethod
    def _concat(self, data_list):
        """How to concatenate multiple elements"""
        pass

    @abstractmethod
    def _slice(self, data, n, end=False):
        """How to slice the elements, e.g. for a numpy array x[:n]"""
        pass

    @abstractmethod
    def __len__(self):
        pass

    def view(self, n=None):
        """View the buffer"""
        return self._data if n is None else self._slice(self._data, n)

    def extend(self, data):
        """Appends data to the buffer and pops off and slices s.t. the length matches maxlen"""
        self._init_cols_if_needed(data)
        self._validate(data)
        self._data = self._concat([self._data, data])

        if self.maxlen is None:
            return

        self._data = self._slice(self._data, self.maxlen, end=True)

    def popleft(self, n):
        """Pops n elements from the left of the buffer.

        If the user asks for more elements than there are on the buffer it will return all the buffer except if
        the buffer is empty it raises an error
        """
        if n == 0:
            return self._empty()
        if len(self) == 0:
            raise IndexError("Pop from empty buffer")
        data_out = self._slice(self._data, n)
        n_to_keep = self._data.shape[-1] - n
        self._data = self._slice(self._data, n_to_keep, end=True) if n_to_keep > 0 else self._empty()
        return data_out

    def popleft_all(self):
        return self.popleft(len(self))

    def __repr__(self):
        return f"{self.__class__.__name__}({self.maxlen, self.cols})"


class DataBuffer(MutableMapping, Buffer):
    """
    A buffer that stores data in a dict of numpy arrays.
    The arrays can have an arbitrary number of dimensions with any shapes, but
    the last dimension is synced across the arrays and is the buffer dimension.
    If maxlen is set, the buffer will be sliced to that length along the last dimension.
    """

    # ========================
    #  Direct dict operations
    # ========================
    def __init__(self, maxlen=None, data=None):
        super().__init__(maxlen, None)

        self._data = data if data is not None else {}
        self.charts = []
        if self.maxlen is not None and len(self) > maxlen:
            self._data = _slice(self._data, self.maxlen, end=True)

    def __len__(self):
        if self._data == {}:
            return 0
        return max(v.shape[-1] for v in self._data.values())

    def __getitem__(self, k):
        if k not in self.keys():
            m = re.match(r"(.+)_(\d+)", k)
            if m is not None:
                key, index = m.groups()
                return self._data[key][int(index)]
            else:
                raise KeyError(f"Key {k} not found in {self.keys()}")
        return self._data[k]

    def __setitem__(self, key, value):
        self._data[key] = value

    def _add_series(self, key, value, max_size=None):
        if max_size is None:
            max_size = self.maxlen
        if max_size is not None and len(value) > max_size:
            value = value[-max_size:]
        self._data[key] = value

    def __delitem__(self, v):
        del self._data[v]

    def __iter__(self):
        return iter(self._data)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def clear(self):
        self._data = {}

    def __copy__(self):
        return DataBuffer(self.maxlen, self._data.copy())

    def copy(self):
        return self.__copy__()

    def _init_cols_if_needed(self, data):
        if len(self) == 0:
            self._data = {k: np.empty((*v.shape[:-1], 0), dtype=v.dtype) for k, v in data.items()}

    # ========================
    #  Buffer operations
    # ========================

    def extend(self, data):
        """Appends data to the buffer and pops off and slices s.t. the length matches maxlen"""
        super().extend(data)
        self._update_charts()

    def _empty(self):
        return {}

    def _validate(self, data):
        pass

    def _concat(self, data_list):
        result, new = data_list
        for k, v in new.items():
            if k in result.keys():
                try:
                    result[k] = np.concatenate([result[k], v], axis=-1)
                except ValueError as e:
                    logger.exception(f"Error concatenating {k=}")
                    raise e
            else:
                result[k] = v
        return result

    def _slice(self, data, n, end=False):
        return _slice(data, n, end)

    def append(self, pt):
        pts = {k: np.array([v]).T for k, v in pt.items()}
        self.extend(pts)

    # =========
    # Plotting
    # =========

    def plot(self, key, plot_type="chart", **kwargs):
        if plot_type == "chart":
            return self._plot_line_chart(key, **kwargs)
        elif plot_type == "spectrogram":
            return self._plot_spectrogram(key, **kwargs)
        elif plot_type == "trace2D":
            return self._plot_trace(key, **kwargs)
        elif plot_type == "histogram":
            return self._plot_histogram(key, **kwargs)
        elif plot_type == "video":
            return self._plot_video(key, **kwargs)

    def _update_charts(self):
        for chart in self.charts:
            if chart["type"] == "line":
                self._update_line_chart(chart)
            elif chart["type"] == "spectrogram":
                self._update_spectrogram(chart)
            elif chart["type"] == "trace2D":
                self._update_trace(chart)
            elif chart["type"] == "histogram":
                self._update_histogram(chart)
            elif chart["type"] == "video":
                self._update_video(chart)

    def _plot_video(self, key):
        frame = Image(format="jpeg")
        obj = {"type": "video", "key": key, "frame": frame}
        self._update_video(obj)
        self.charts.append(obj)
        return frame

    def _update_video(self, obj):
        key = obj["key"]
        frame = obj["frame"]
        value = self[key][..., -1].transpose(2, 1, 0)
        _, jpeg_image = cv2.imencode(".jpeg", value)
        frame.value = jpeg_image.tobytes()

    def _plot_line_chart(self, key, x_key=None):
        xs = bq.LinearScale()
        ys = bq.LinearScale()
        xax = bq.Axis(scale=xs, label="t")
        yax = bq.Axis(scale=ys, orientation="vertical", label=key)
        line = bq.Lines(x=[], y=[], scales={"x": xs, "y": ys})
        fig = bq.Figure(marks=[line], axes=[xax, yax])
        chart_obj = {"type": "line", "key": key, "line": line, "x_key": x_key}
        # Call _update_line_chart first, if there is an error
        # we won't add the chart to self.charts
        self._update_line_chart(chart_obj)
        self.charts.append(chart_obj)
        return fig

    def _update_line_chart(self, chart):
        key = chart["key"]
        line = chart["line"]
        x_key = chart["x_key"]
        if x_key is None:
            line.x = np.arange(len(self))
        else:
            line.x = self[x_key]
        line.y = self[key]

    def _plot_spectrogram(self, key, **kwargs):
        xs = bq.LinearScale()
        ys = bq.LinearScale()
        xax = bq.Axis(scale=xs, label="Hz")
        yax = bq.Axis(scale=ys, orientation="vertical", label="db")
        # data is assumed to be complex-valued array of shape (t, f)
        # We only use the latest point, and simply plot the magnitude
        line = bq.Lines(x=[], y=[], scales={"x": xs, "y": ys})
        chart_obj = {
            "type": "spectrogram",
            "key": key,
            "line": line,
            "sample_rate": kwargs.get("sample_rate", 1),  # Is there a sensible default?
            "window_size": kwargs.get("window_size", 1),  # Is there a sensible default?
        }
        fig = bq.Figure(marks=[line], axes=[xax, yax])
        # Call _update_spectrogram first, if there is an error
        # we won't add the chart to self.charts
        self._update_spectrogram(chart_obj)
        self.charts.append(chart_obj)
        return fig

    def _update_spectrogram(self, chart):
        key = chart["key"]
        line = chart["line"]
        sample_rate = chart["sample_rate"]
        window_size = chart["window_size"]
        data = self[key][..., -1]
        omega = np.fft.rfftfreq(window_size, 1 / sample_rate)
        line.x = omega
        line.y = 10 * np.log10(np.maximum(np.abs(data), 1e-20))

    def _plot_trace(self, key):
        xs = bq.LinearScale()
        ys = bq.LinearScale()
        xax = bq.Axis(scale=xs, label="x")
        yax = bq.Axis(scale=ys, orientation="vertical", label="y")
        line = bq.Lines(x=[], y=[], scales={"x": xs, "y": ys})
        fig = bq.Figure(marks=[line], axes=[xax, yax])
        chart_obj = {"type": "trace2D", "key": key, "line": line}
        # Call _update_line_chart first, if there is an error
        # we won't add the chart to self.charts
        self._update_trace(chart_obj)
        self.charts.append(chart_obj)
        return fig

    def _update_trace(self, chart):
        key = chart["key"]
        line = chart["line"]
        # We need to change the x and y axis atomically to avoid flickering in the plot
        with line.hold_sync():
            line.x = self[key][0]
            line.y = -self[key][1]

    def _plot_histogram(self, key, **kwargs):
        x_names = kwargs.get("class_names", None)
        xs = bq.OrdinalScale()
        ys = bq.LinearScale()
        xax = bq.Axis(scale=xs)
        yax = bq.Axis(scale=ys, orientation="vertical", label="Probability")
        bars = bq.Bars(x=x_names, y=[], scales={"x": xs, "y": ys})
        fig = bq.Figure(marks=[bars], axes=[xax, yax])
        chart_obj = {"type": "histogram", "key": key, "bars": bars}
        # Call _update_histogram first, if there is an error
        # we won't add the chart to self.charts
        self._update_histogram(chart_obj)
        self.charts.append(chart_obj)
        return fig

    def _update_histogram(self, chart):
        key = chart["key"]
        bars = chart["bars"]
        bars.y = self[key][..., -1]

    # ==============
    # Serialization
    # ==============

    @classmethod
    def from_dataframe(cls, df, maxlen=None):
        return cls(maxlen=maxlen, data={k: df[k].values for k in df.columns})

    def to_dataframe(self):
        flat_data = {}
        for k, v in self._data.items():
            if v.ndim == 1:
                flat_data[k] = v
            elif v.ndim == 2:
                for i in range(v.shape[0]):
                    flat_data[f"{k}_{i}"] = v[i]
            elif v.ndim == 3:
                for i in range(v.shape[0]):
                    for j in range(v.shape[1]):
                        flat_data[f"{k}_{i}_{j}"] = v[i, j]
            else:
                raise ValueError(f"Can't flatten data with ndim={v.ndim}")
        return pd.DataFrame(flat_data)

    def to_arrow(self):
        # TODO
        raise NotImplementedError

    def as_dict(self):
        return self._data

    def __repr__(self):
        data_str = "\n".join(f"{k}: {v.shape}" for k, v in self._data.items())
        return f"DataBuffer(max_size={self.maxlen}, data={data_str})"


class PandasBuffer(Buffer):
    def _empty(self):
        return pd.DataFrame()

    def _init_cols_if_needed(self, data):
        if self.cols is None:
            self.cols = data.columns

    def _validate(self, data):
        assert set(data.columns) == set(self.cols), f"Expected the same columns. Got {data.columns=} and {self.cols}"

    def _slice(self, data, n, end=False):
        return data.iloc[-n:] if end else data.iloc[:n]

    def _concat(self, data_list):
        return pd.concat(data_list, axis=0)


class NumpyBuffer(Buffer):
    def __init__(self, maxlen, n_cols=None):
        if isinstance(n_cols, int):
            n_cols = (n_cols,)
        self.cols = n_cols
        super().__init__(maxlen, n_cols)

    def __len__(self):
        return self._data.shape[-1]

    def _init_cols_if_needed(self, data):
        # don't set cols for empty data
        if data.shape[-1] == 0:
            return
        if self.cols is None:
            self.cols = data.shape[:-1]

    def _empty(self):
        if self.cols is None:
            return np.empty((0, 0))
        return np.empty((*self.cols, 0))

    def _validate(self, data):
        # don't validate empty data
        if data.shape[-1] == 0:
            return
        assert data.shape[:-1] == self.cols, (
            "Expected a fixed number of cols to be able to concatenate " f"got {data.shape=} with {self.cols=}"
        )

    def _slice(self, data, n, end=False):
        return data[..., -n:] if end else data[..., :n]

    def _concat(self, data_list):
        if all(d.size == 0 for d in data_list):
            return self._empty()
        return np.concatenate([d for d in data_list if d.size != 0], axis=-1)

    def append(self, pt):
        """Append a single point to the buffer"""
        pt = np.asarray(pt)
        self.extend(pt[..., None])

    def __repr__(self):
        return f"{self.__class__.__name__}({self.maxlen, self._data.shape})"
