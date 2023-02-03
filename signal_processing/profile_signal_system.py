"""
Simple function to profile SignalSystem
use with timeit e.g.:
    `python -m timeit -s 'from wave_ml.signal_processing.profile_signal_system import test' 'test()'`
"""
import math
import string

import numpy as np
import pandas as pd

from .data_sources import DataFrameDataSource
from . import signals as s
from .system import SignalSystem


def test(n_cols=10, n_rows=10000, lines_per_read=5):
    data = np.random.rand(n_rows, n_cols)
    cols = list(string.ascii_letters[:n_cols])
    df = pd.DataFrame(data, columns=cols, index=range(n_rows))

    # Bunch of random derived signals
    derived = [
        s.Difference("a", "b", name="a-b"),
        s.Integrate("c", name="int(c)"),
        s.GaussianSmooth("e", 1.0, fs=100, name="smooth e"),
        s.Scale("f", 5, name="5f"),
        s.HighPassFilter("g_filt", "g", 2, 10),
        s.LowPassFilter("h_filt", "h", 2, 10),
        s.Multiply("i", "j", "j * i"),
    ]
    source = DataFrameDataSource(df, lines_per_read=lines_per_read)
    system = SignalSystem(source, derived)

    with system:
        for _ in range(math.ceil(n_rows / lines_per_read)):
            system.view()


if __name__ == "__main__":
    test()
