from pathlib import Path

import pandas as pd

from genki_signals.buffers import DataBuffer
from genki_signals.data_sources.base import SamplerBase


class DataFrameDataSource(SamplerBase):
    """
    A way to use a pandas DataFrame that has been loaded into memory as a DataSource.
    The way this works is, on each call to read(), the same number of lines are read from the DataFrame.
    """
    def __init__(self, df, lines_per_read=5):
        self.current_line = None
        self.data = df
        self.lines_per_read = lines_per_read

    def start(self):
        self.current_line = 0
        self._load_chunk()

    def start_recording(self, *args):
        raise Exception(
            "Recording from {self.__class__.__name__} to a file is not supported \
                    and probably not something you want do be doing?"
        )

    def stop(self):
        pass

    def _load_chunk(self):
        if self.lines_per_read < 0:
            data = self.data
        else:
            data = self.data.iloc[
               self.current_line:self.current_line + self.lines_per_read
           ]
        self.next_chunk = DataBuffer.from_dataframe(data)

    def read(self):
        if not hasattr(self, "current_line"):
            raise Exception(
                "Tried to call read() from a data source that has not been started."
            )
        chunk = self.next_chunk
        self.current_line += len(list(chunk.values())[0])
        self._load_chunk()
        return chunk

    def signal_names(self):
        return list(self.next_chunk.keys())


class FileDataSource(DataFrameDataSource):
    def __init__(self, filename, lines_per_read=5, line_offset=0):
        self.path = Path(filename)

        if self.path.suffix == ".csv":
            data = pd.read_csv(self.path)
        elif self.path.suffix == ".pkl":
            data = pd.read_pickle(self.path)
        elif self.path.suffix == ".parquet":
            data = pd.read_parquet(self.path)
        else:
            raise Exception(
                f"Suffix {self.path.suffix} not supported for FileDataSource (Path: {self.path})"
            )
        data = data.iloc[line_offset:]
        super().__init__(data, lines_per_read)

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.path}>"

    def _repr_markdown_(self):
        return self.__repr__()


class SessionDataSource(DataFrameDataSource):
    def __init__(self, session, lines_per_read=-1):
        super().__init__(session.df, lines_per_read)

