from __future__ import annotations

import getpass
import glob
import json
import pickle
import sys
from datetime import datetime
from pathlib import Path
import wave
import numpy as np

from genki_signals.buffers import DataBuffer
from genki_signals.signal_functions.serialization import encode_signal_fn, decode_signal_fn


def read_json_file(p: Path | str):
    with open(p, "r") as FILE:
        return json.load(FILE, object_hook=decode_signal_fn)


def write_json_file(p: Path | str, data: dict | list):
    with open(p, "w") as FILE:
        json.dump(data, FILE, indent=4, default=encode_signal_fn)


class Session:
    """Encapsulates data for a single recorded session, includes metadata.
    Use `Session.from_filename` to load a session.

    Each Session object corresponds to a directory with the following structure:

    session
    |-- raw_data.pickle
    |-- metadata.json

    The file raw_data.pickle (can also be other formats, e.g. wav and parquet)
    contains the raw data recorded during the session, and is read-only.

    The file metadata.json contains various metadata about the session, and
    can be modified by the `Session` object.
    """

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.session_name = self.base_path.name
        self._raw_data_path = None
        self._datafile_extension = None
        self._metadata = None
        self._data = None

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.session_name}>"

    @classmethod
    def from_filename(cls, path: Path | str):
        """Instantiate Session, `path` should be a directory containing a
        raw_data file and metadata.json."""
        return cls(Path(path))

    @classmethod
    def create_session(cls, path, system, metadata):
        """
        Create an empty session, sets up directory structure but writes no
        raw data file, just metadata.
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=False)

        metadata["session_name"] = path.name
        metadata["system_user"] = getpass.getuser()
        metadata["timestamp"] = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        metadata["argv"] = sys.argv
        metadata["platform"] = sys.platform
        metadata["data_source"] = system.source.__class__.__name__
        metadata["sample_rate"] = system.source.sample_rate
        metadata["signal_functions"] = system.signal_functions

        self = cls(path)

        write_json_file(self.metadata_path, metadata)
        self._load_metadata()

        return self

    # ==========
    #  File I/O
    # ==========

    def _load_data(self):
        if self.datafile_extension in [".pickle", ".pkl"]:
            with open(self.raw_data_path, "rb") as FILE:
                self._data = pickle.load(FILE)
        elif self.datafile_extension == ".wav":
            wavefile = wave.open(self.raw_data_path.as_posix(), "rb")
            data = wavefile.readframes(wavefile.getnframes())
            self._data = DataBuffer(data={"audio": np.frombuffer(data, np.int16)})
        else:
            raise NotImplementedError(f"Loading data from {self._datafile_extension} is not implemented")

    def _load_metadata(self):
        self._metadata = read_json_file(self.metadata_path)

    def _write_metadata(self):
        write_json_file(self.metadata_path, self.metadata)

    def _find_raw_data_file(self):
        found = glob.glob(str(self.base_path / "raw_data.*"))
        if len(found) == 0:
            raise FileNotFoundError("No raw data file found")
        elif len(found) > 1:
            raise FileNotFoundError("Multiple raw data files found")
        else:
            raw_data_path = Path(found[0])
            self._raw_data_path = raw_data_path
            self._datafile_extension = raw_data_path.suffix

    # ===================
    #  Data/Metadata API
    # ===================

    @property
    def datafile_extension(self):
        if self._datafile_extension is None:
            self._find_raw_data_file()
        return self._datafile_extension

    @property
    def raw_data_path(self):
        if self._raw_data_path is None:
            self._find_raw_data_file()
        return self._raw_data_path

    @property
    def metadata_path(self):
        return self.base_path / "metadata.json"

    @property
    def metadata(self):
        if self._metadata is None:
            self._load_metadata()
        return self._metadata

    @property
    def data(self):
        if self._data is None:
            self._load_data()
        return self._data

    def add_metadata_field(self, name: str, value):
        self.metadata[name] = value
        self._write_metadata()
