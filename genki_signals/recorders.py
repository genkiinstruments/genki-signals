"""
This module contains classes for recording data.
"""
import abc
import pickle
import wave

from genki_signals.buffers import DataBuffer


class Recorder(abc.ABC):
    @abc.abstractmethod
    def write(self, data: DataBuffer):
        pass

    @abc.abstractmethod
    def stop(self):
        pass


class PickleRecorder(Recorder):
    def __init__(self, path, rec_buffer_size=1_000_000):
        self.path = path
        self.rec_buffer_size = rec_buffer_size
        self._has_written_file = False
        self._recording_buffer = DataBuffer()

    def write(self, data: DataBuffer):
        self._recording_buffer.extend(data)
        if len(self._recording_buffer) > self.rec_buffer_size:
            self._flush_to_file()

    def stop(self):
        self._flush_to_file()

    def _flush_to_file(self):
        if self._has_written_file:
            with open(self.path, "rb") as f:
                old_data = pickle.load(f)
                data = old_data.extend(self._recording_buffer)
        else:
            data = self._recording_buffer
        with open(self.path, "wb") as f:
            pickle.dump(data, f)
            self._has_written_file = True
        self._recording_buffer.clear()


class WavFileRecorder(Recorder):
    def __init__(self, path, frame_rate, n_channels, sample_width):
        self.path = path
        self.wavefile = wave.open(self.path, "wb")
        self.wavefile.setframerate(frame_rate)
        self.wavefile.setnchannels(n_channels)
        self.wavefile.setsampwidth(sample_width)

    def write(self, data: DataBuffer):
        self.wavefile.writeframes(data["audio"].tobytes())

    def stop(self):
        self.wavefile.close()


class DataFrameRecorder(Recorder):
    def __init__(self, path, rec_buffer_size=1_000_000):
        self.path = path
        self.rec_buffer_size = rec_buffer_size
        self._has_written_file = False
        self._recording_buffer = DataBuffer()

    def _flush_to_file(self):
        df = self._recording_buffer.to_dataframe()
        if self._has_written_file:
            self.serialize_frame(df, initial_frame=False)
        else:
            self.serialize_frame(df, initial_frame=True)
            self._has_written_file = True
        self._recording_buffer.clear()

    @abc.abstractmethod
    def serialize_frame(self, frame, initial_frame=False):
        pass

    def write(self, data: DataBuffer):
        self._recording_buffer.extend(data)
        if len(self._recording_buffer) > self.rec_buffer_size:
            self._flush_to_file()

    def stop(self):
        self._flush_to_file()


class CsvFileRecorder(DataFrameRecorder):
    def serialize_frame(self, df, initial_frame=False):
        if initial_frame:
            df.to_csv(self.path, index=False)
        else:
            df.to_csv(self.path, mode="a", header=False, index=False)


class ParquetFileRecorder(DataFrameRecorder):
    def serialize_frame(self, df, initial_frame=False):
        if initial_frame:
            df.to_parquet(self.path, index=False)
        else:
            df.to_parquet(self.path, mode="a", index=False)