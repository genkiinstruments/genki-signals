from __future__ import annotations

import pstats
import io
from cProfile import Profile
from pstats import SortKey
import numpy as np
import time
import yappi
import pandas as pd
import wandb
import matplotlib as mpl
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from genki_signals.buffers import DataBuffer
from genki_signals.system import System
from genki_signals.buffers import Buffer


def profile_buffer(buffer: DataBuffer, data: dict[str, np.ndarray], it : int = 10000, read_buffer_rate : int = np.inf):
    _buffer = buffer.copy()
    profiler = Profile()
    profiler.enable()
    for i in range(1, it + 1):
        _buffer.extend(data)
        if i % read_buffer_rate == 0:
            _ = _buffer.copy()
            _buffer.clear()
    profiler.disable()
    stats = pstats.Stats(profiler, stream=io.StringIO()).sort_stats(SortKey.CUMULATIVE).get_stats_profile()
    keys = ["extend", "copy", "clear"]
    stats = {key: stats.func_profiles[key] for key in keys}
    # func_stats = {key: 1000 * value.cumtime / int(value.ncalls) for key, value in stats.items()}
    func_stats = {key: 1000 * value.cumtime for key, value in stats.items()}
    return {
        **func_stats,
        "total": 1000 * sum([stats[key].cumtime for key in stats]),
    }


buffer_tests = [
    {
        "data": {"input": np.array([3.14])},
        "it": 100000,
        "read_buffer_rate": 10000
    },
    {
        "data": {"input": np.random.rand(100, 100)},
        "it": 20,
        "read_buffer_rate": 2
    },
    {
        "data": {"input": np.random.rand(1024)},
        "it": 100,
        "read_buffer_rate": 3
    },
    {
        "data": {f"input_{i}": np.random.rand(100) for i in range(100)},
        "it": 100,
        "read_buffer_rate": 1,
    },
    {
        "data": {f"input_{i}": np.random.rand(3, 10) for i in range(3)},
        "it": 30000,
        "read_buffer_rate": 5
    },
    {
        "data": {"input": np.random.rand(3, 1000000)},
        "it": 3,
        "read_buffer_rate": 1
    }
]


def compare_buffers(
        buffers : list[Buffer],
        buffer_names : list[str] | None = None,
        logger_config : dict[str, Any] = None,
        verbose : bool = False,
):
    if buffer_names is None:
        buffer_names = [f"buffer_{i}" for i in range(len(buffers))]
    assert len(buffer_names) == len(buffers)
    eps = np.finfo(np.float32).eps
    tests = []
    if logger_config is not None:
        mpl.rcParams['figure.dpi'] = 300
        wandb.init(**logger_config)
        images = []
    for i, test in enumerate(buffer_tests):
        stats = [profile_buffer(buffer, **test) for buffer in buffers]
        if len(stats) == 2:
            diff = {key: (stats[0][key] + eps) / (stats[1][key] + eps) for key in stats[0]}
            df = pd.DataFrame([*stats, diff])
            df["name"] = [*buffer_names, "performance ratio"]
        else:
            df = pd.DataFrame(stats)
            df["name"] = buffer_names
        shape_of_array = list(test["data"].values())[0].shape
        description = f'packet size: {len(test["data"])}x{shape_of_array}, read_frequency: {test["read_buffer_rate"]}'
        df["test"] = i
        df["test_description"] = description
        tests.append(df)
        if logger_config is not None:
            log_df = pd.DataFrame(stats)
            log_df.index = buffer_names
            ax = log_df.plot(
                y=log_df.columns,
                kind="bar",
                rot=0,
                use_index=True,
                logy=True,
                ylabel="ms",
                title=description
            )
            images.append(wandb.Image(ax.get_figure(), caption=description))
        if verbose:
            print(f"buffer test {i}:")
            print(df)
            print()
            print()
    if logger_config is not None:
        wandb.log({"buffer_tests": images})
        wandb.finish()
    return pd.concat(tests)


def profile_system(system: System, t : float = 1.0, verbose : bool = False):
    yappi.set_clock_type("cpu")  # Use set_clock_type("wall") for wall time
    yappi.start()
    system.start()

    time.sleep(t)

    system.stop()
    yappi.stop()
    stats = yappi.get_func_stats()

    df = pd.DataFrame(stats)
    df.columns = stats[0]._KEYS
    df_filtered = df[["name", "ncall", "ttot", "tsub", "tavg"]]

    if verbose:
        print(df_filtered.to_string())

    return df_filtered


def compare_systems(systems: list[System], t: float = 1.0, names: list[str] | None = None, verbose: bool = False,):
    if names is None:
        names = [f"system_{i}" for i in range(len(systems))]
    assert len(names) == len(systems)

    dfs = []
    for i, system in enumerate(systems):
        df = profile_system(system, t, verbose=False)
        if verbose:
            print(names[i])
            print(df.to_string(), end="\n\n\n")
        df["system"] = names[i]
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)
