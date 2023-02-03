import re
from collections.abc import MutableMapping
from collections import defaultdict

import pandas as pd
import numpy as np

DIMENSION_POSTFIXES = {2: ["x", "y"], 3: ["x", "y", "z"], 4: ["w", "x", "y", "z"]}


def dict_value_to_array(value):
    if isinstance(value, np.ndarray) and value.ndim == 1:
        return value[None]
    elif isinstance(value, np.ndarray):
        return value
    elif isinstance(value, list):
        return dict_value_to_array(np.array(value, dtype=float))
    elif isinstance(value, dict):
        # TODO: what about euler pitch, roll, yaw?
        # assert any(list(value.keys()) == list(v) for v in DIMENSION_POSTFIXES.values()), value
        return dict_value_to_array(list(value.values()))
    else:
        return dict_value_to_array([value])


class ArrayFrame(MutableMapping):
    """
    Mapping: dict[str, array[n, *k]] (n is time, k vector dimension)
    """

    def __init__(self, *args, **kw):
        self.data = dict(*args, **kw)
        if len(self.data) == 0:
            self._length = 0
            return

        self._length = max(len(v) for v in self.data.values())
        self._assert_length()

    def __getitem__(self, key):
        if isinstance(key, (list, tuple)):
            return np.concatenate([self.data[k] for k in key], axis=1)
        return self.data[key]

    def _assert_length(self):
        for k, v in self.items():
            assert (
                len(v) == self._length
            ), f"All arrays in ArrayFrame must have same length, {k=} has length {len(v)} which \
            doesnt match {self._length=}"

    def __setitem__(self, key, value):
        if len(self) == 0:
            self.data = {key: value}
            self._length = len(value)
        else:
            self.data[key] = value
            self._assert_length()

    def __delitem__(self, key):
        del self.data[key]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return self._length

    def __repr__(self):
        return "ArrayFrame{" + ", ".join(f"{k}: {v}" for k, v in self.items()) + "}"

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    def clear(self):
        self.data = {}
        self._length = 0

    def append(self, pt: dict):
        if len(self) == 0:
            self.data = {}
            for key, val in pt.items():
                arr_val = dict_value_to_array(val)
                self.data[key] = arr_val
                added_length = len(arr_val)
        else:
            assert pt.keys() == self.keys()
            for key, val in pt.items():
                arr_val = dict_value_to_array(val)
                assert self[key].shape[1:] == arr_val.shape[1:], ""
                self.data[key] = np.concatenate([self[key], arr_val], axis=0)
                added_length = len(arr_val)
        self._length += added_length
        self._assert_length()

    def extend(self, frame):
        if len(self) == 0:
            self.data = {}
            for key, val in frame.items():
                self[key] = val
        else:
            assert frame.keys() == self.keys()
            for key, val in frame.items():
                self.data[key] = np.concatenate([self[key], val], axis=0)
                added_length = len(val)
            self._length += added_length
        self._assert_length()

    def as_dataframe(self):
        result = pd.DataFrame()
        for key, val in self.items():
            if val.ndim == 2 and val.shape[1] == 1:
                result[key] = val[:, 0]
            elif val.ndim == 2 and val.shape[1] in DIMENSION_POSTFIXES.keys():
                for i, postfix in enumerate(DIMENSION_POSTFIXES[val.shape[1]]):
                    result[f"{key}_{postfix}"] = val[:, i]
            else:
                result[key] = val.tolist()
        return result

    @classmethod
    def from_dataframe(cls, df):
        vector_prefixes = []
        for key in df.columns:
            if m := re.match(r"(.+)_x.*", key):
                vector_prefixes.append(m.groups()[0])
        df_keys = defaultdict(list)
        for key in df.columns:
            prefixes = [p for p in vector_prefixes if key.startswith(p)]
            if len(prefixes) > 0:
                longest_prefix = max(prefixes, key=len)
                df_keys[longest_prefix].append(key)
            else:
                df_keys[key].append(key)
        result = {}
        for key, columns in df_keys.items():
            result[key] = df[columns].values
        return cls(result)

    def as_dict(self):
        return self.data
