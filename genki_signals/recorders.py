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
        self._recording_buffer.append(data)
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
    def __init__(self, path, n_channels, sample_width, frame_rate):
        self.path = path
        self.wavefile = wave.open(self.path, "wb")
        self.wavefile.setnchannels(n_channels)
        self.wavefile.setsampwidth(sample_width)
        self.wavefile.setframerate(frame_rate)

    def write(self, data: DataBuffer):
        self.wavefile.writeframes(data['audio'].to_bytes())

    def stop(self):
        self.wavefile.close()


class CsvFileRecorder(Recorder):
    def __init__(self, path, rec_buffer_size=1_000_000):
        self.path = path
        self.rec_buffer_size = rec_buffer_size
        self._has_written_file = False
        self._recording_buffer = DataBuffer()

    def _flush_to_file(self):
        df = self._recording_buffer.to_dataframe()
        if self._has_written_file:
            df.to_csv(self.path, mode='a', header=False, index=False)
        else:
            df.to_csv(self.path, index=False)
            self._has_written_file = True
        self._recording_buffer.clear()

    def write(self, data: DataBuffer):
        self._recording_buffer.extend(data)
        if len(self._recording_buffer) > self.rec_buffer_size:
            self._flush_to_file()

    def stop(self):
        self._flush_to_file()
