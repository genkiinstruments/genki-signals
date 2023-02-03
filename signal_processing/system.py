import math
import logging
from collections import OrderedDict
from collections.abc import MutableMapping
from datetime import datetime

from more_itertools import flatten

from signal_processing.buffers import NumpyBuffer
from signal_processing.array_frame import ArrayFrame

logger = logging.getLogger(__name__)


def upsample(signal, factor):
    # Note that we can potentially use other methods for upsampling e.g. interpolation
    return signal.repeat(factor, axis=0)


class SignalSystem:
    """
    A SignalSystem is a DataSource with a list of derived signals. The system
    collects data points as they arrive from the source, computes derived signals,
    and stores everything in a fixed length buffer. The buffer thus provides
    a sliding window view of the system, accessed with the view() method.
    """

    def __init__(self, data_source, derived, buffer_len=400):
        self.derived_signals = OrderedDict((s.name, s) for s in derived)
        self.source = data_source
        self.buffer_len = buffer_len

    def start(self):
        self.start_time = datetime.now()
        self.source.start()
        output_columns = [
            [k] if not hasattr(s, "outputs") else s.outputs
            for k, s in self.derived_signals.items()
        ]
        output_columns = list(flatten(output_columns))
        self.buffers = dict(
            (name, NumpyBuffer(self.buffer_len, None))
            for name in self.source.signal_names()
        )
        for signal_name, signal in self.derived_signals.items():
            output_names = (
                [signal_name] if not hasattr(signal, "outputs") else signal.outputs
            )
            for name in output_names:
                freq_ratio = signal.frequency_ratio
                buffer_len = (
                    math.ceil(self.buffer_len / freq_ratio)
                    if self.buffer_len is not None
                    else None
                )
                self.buffers[name] = NumpyBuffer(buffer_len, None)

    def stop(self):
        self.source.stop()
        self.stop_time = datetime.now()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

    def _fetch_data(self, data, names):
        return tuple(data[name] for name in names)

    def _compute_derived(self, data: dict):
        for signal in self.derived_signals.values():
            inputs = self._fetch_data(data, signal.input_names)
            # TODO: error reporting here? Remove ill-behaved signals?
            output = signal(*inputs)
            if isinstance(output, MutableMapping):
                data.update(output)
            else:
                data[signal.name] = output

    def _read_new(self):
        data = self.source.read().as_dict()
        if len(data) > 0:
            self._compute_derived(data)
        return data

    def _update(self):
        new_data = self._read_new()
        for name, data in new_data.items():
            try:
                self.buffers[name].extend(data)
            except AssertionError as e:
                print(f"Failed to insert {name} to buffer")
                raise e
        return new_data

    def view(self, as_dataframe=True):
        # This no longer returns a DataFrame, but a dictionary from name -> ndarray.
        # No upsampling involved.
        self._update()

        frame = ArrayFrame()
        for name, buffer in self.buffers.items():
            data = buffer.view()
            if name in self.derived_signals:
                freq_ratio = self.derived_signals[name].frequency_ratio
            else:
                freq_ratio = 1
            if freq_ratio > 1:
                data = upsample(data, freq_ratio)
                data = data[-len(frame) :]
            frame[name] = data

        if as_dataframe:
            return frame.as_dataframe()
        return frame

    def read(self, as_dataframe=True):
        """
        Return all new data points received since the last call to read() or view()
        """
        data = self._update()
        if as_dataframe:
            return ArrayFrame(data).as_dataframe()
        return data

    def __repr__(self):
        return f"<SignalSystem, source: {self.source}, buffer_len: {self.buffer_len}>"

    def _repr_markdown_(self):
        derived = ",".join(f"`{s.name}`" for s in self.derived_signals)
        return (
            f"| {self.__class__.__name__} ||\n"
            "| --- | --- |\n"
            f"| Source | {self.source._repr_markdown_()} |\n"
            f"| Derived | {derived}"
        )
