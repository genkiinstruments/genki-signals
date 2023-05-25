import logging
import re
from abc import ABC, abstractmethod
from collections.abc import MutableMapping

import numpy as np
import pandas as pd

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

    # ==============
    # Serialization
    # ==============

    @classmethod
    def from_dataframe(cls, df, maxlen=None):
        split = re.compile(r"(?P<name>\D+)_(?P<number>(\d+)(_\d+)?(_\d+)?)")
        data = {}
        composite_data = {}
        for col in df.columns:
            m = split.match(col)
            if m is not None:
                name, number = m.groupdict()['name'], m.groupdict()['number']
                number = tuple(map(int, number.split("_")))
                if name not in composite_data:
                    composite_data[name] = []
                composite_data[name].append((number, df[col].values))
            else:
                data[col] = df[col].values
        for name, values in composite_data.items():
            values = sorted(values, key=lambda x: x[0])
            pt_shape = tuple(d+1 for d in values[-1][0])
            t_shape = values[0][1].shape
            arr = np.zeros((*pt_shape, *t_shape), dtype=values[0][1].dtype)
            for idx, pts in values:
                arr[idx] = pts
            data[name] = arr
        return cls(maxlen=maxlen, data=data)

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
