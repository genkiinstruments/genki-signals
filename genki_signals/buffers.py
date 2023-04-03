from abc import ABC, abstractmethod
from collections.abc import MutableMapping
import re

import numpy as np
import pandas as pd
import bqplot as bq

from genki_widgets import Line, Bar, Trace, Spectrogram


def _slice(data, length, end=True):
    if end:
        return {k: v[..., -length:] for k, v in data.items()}
    else:
        return {k: v[..., :length] for k, v in data.items()}


class DataBuffer(MutableMapping):
    """

    """
    def __init__(self, max_size=None, data=None):
        if max_size is not None and max_size < 1:
            raise ValueError("Length of buffer has to be at least 1")
        self.max_size = max_size
        self.data = data if data is not None else {}

        self.on_extend_callbacks = []

        if self.max_size is not None and len(self) > max_size:
            self.data = _slice(self.data, self.max_size, end=True)

    def __len__(self):
        if self.data == {}:
            return 0
        return max(v.shape[-1] for v in self.data.values())

    def __getitem__(self, k):
        if k not in self.keys():
            m = re.match(r"(.+)_(\d+)", k)
            if m is not None:
                key, index = m.groups()
                return self.data[key][int(index)]
            else:
                raise KeyError(f"Key {k} not found in {self.keys()}")
        return self.data[k]

    def __setitem__(self, key, value):
        self.data[key] = value

    def _add_series(self, key, value, max_size=None):
        if max_size is None:
            max_size = self.max_size
        if max_size is not None and len(value) > max_size:
            value = value[-max_size:]
        self.data[key] = value

    def __delitem__(self, v):
        del self.data[v]

    def __iter__(self):
        return iter(self.data)

    def _init_cols_if_needed(self, data):
        if len(self) == 0:
            self.data = {k: np.empty((*v.shape[:-1], 0)) for k, v in data.items()}

    def add_callback(self, callback):
        self.on_extend_callbacks.append(callback)

    def extend(self, data):
        """Appends data to the buffer and pops off and slices s.t. the length matches maxlen"""
        if len(data) == 0:
            return
        self._init_cols_if_needed(data)
        for k, v in data.items():
            if k in self.keys():
                self[k] = np.concatenate([self[k], v], axis=-1)
            else:
                self[k] = v
        if self.max_size is not None:
            self.data = _slice(self.data, self.max_size, end=True)

        if not isinstance(data, dict):
            data = data.data

        for callback in self.on_extend_callbacks:
            callback(data)

    def append(self, pt):
        pts = {k: np.array([v]).T for k, v in pt.items()}
        self.extend(pts)

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()

    def clear(self):
        self.data = {}

    def __copy__(self):
        return DataBuffer(self.max_size, self.data.copy())

    def copy(self):
        return self.__copy__()

    # ==============
    # Serialization
    # ==============

    @classmethod
    def from_dataframe(cls, df, max_size=None):
        return cls(max_size=max_size, data={k: df[k].values for k in df.columns})

    def to_dataframe(self):
        # TODO
        raise NotImplementedError

    def to_arrow(self):
        # TODO
        raise NotImplementedError

    def __repr__(self):
        data_str = "\n".join(f"{k}: {v.shape}" for k, v in self.data.items())
        return f"DataBuffer(max_size={self.max_size}, data={data_str})"


class Buffer(ABC):
    """deque-like buffer for pandas dataframes and numpy arrays"""

    def __init__(self, maxlen, cols):
        if maxlen is not None and maxlen < 1:
            raise ValueError("Length of buffer has to be at least 1")
        self.maxlen = maxlen
        self.cols = cols
        self._data = self._empty()
        self.chart_lines = []

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

    def __len__(self):
        return len(self._data)

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

        If the user asks for more elements than there are on the buffer it will return all of the buffer except if
        the buffer is empty it raises an error
        """
        if len(self._data) == 0:
            raise IndexError("Pop from empty buffer")
        data_out = self._slice(self._data, n)
        n_to_keep = self._data.shape[-1] - n
        self._data = self._slice(self._data, n_to_keep, end=True) if n_to_keep > 0 else self._empty()
        return data_out

    def popleft_all(self):
        return self.popleft(len(self))

    def __repr__(self):
        return f"{self.__class__.__name__}({self.maxlen, self.cols})"


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

    def _init_cols_if_needed(self, data):
        if self.cols is None:
            self.cols = data.shape[:-1]

    def _empty(self):
        if self.cols is None:
            return np.empty((0, 0))
        return np.empty((*self.cols, 0))

    def _validate(self, data):
        assert data.shape[:-1] == self.cols, ("Expected a fixed number of cols to be able to concatenate "
                                              f"got {data.shape=} with {self.cols=}")

    def _slice(self, data, n, end=False):
        return data[..., -n:] if end else data[..., :n]

    def _concat(self, data_list):
        return np.concatenate([d for d in data_list if d.size != 0], axis=-1)

    def append(self, pt):
        """Append a single point to the buffer"""
        pt = np.asarray(pt)
        self.extend(pt[..., None])

    def __repr__(self):
        return f"{self.__class__.__name__}({self.maxlen, self._data.shape})"

