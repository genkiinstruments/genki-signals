import time
import logging
from pathlib import Path
from threading import Thread

from genki_signals.recorders import PickleRecorder, WavFileRecorder
from genki_signals.session import Session
from genki_signals.functions.base import compute_signal_functions
from genki_signals.sources import MicSource

logger = logging.getLogger(__name__)


class System:
    """
    A System is a source with a list of functions. The system
    collects data points as they arrive from the source, and computes the functions.
    The system update_rate is the rate at which the system will check for new data points,
    specified in Hz. Note that the update_rate will not be exact, as it is limited by the
    use of time.sleep(), so an error of up to 15% is expected.
    """
    def __init__(self, source, functions=None, update_rate=25):
        self.source = source
        self.functions = [] if functions is None else functions
        self.update_rate = update_rate
        self.is_active = False
        self.data_feeds = {}
        self.main_thread = None
        self.recorder = None
        self.is_recording = False

    def __repr__(self):
        return f"System({self.source}, {self.functions})"

    def _busy_loop(self):
        while self.is_active:
            new_data = self._read()
            if len(new_data) > 0:
                # We extract the current data feeds into a list
                # to prevent errors if a feed is deregistered or new feed added
                # while we are iterating over them.
                current_feeds = list(self.data_feeds.values())
                for feed in current_feeds:
                    feed(new_data)
            time.sleep(1 / self.update_rate)

    def register_data_feed(self, feed_id, callback):
        if feed_id in self.data_feeds:
            raise ValueError(f"Feed with id {feed_id} already exists")
        self.data_feeds[feed_id] = callback

    def deregister_data_feed(self, feed_id):
        self.data_feeds.pop(feed_id)

    def start(self):
        self.source.start()
        self.is_active = True
        self.main_thread = Thread(target=self._busy_loop)
        self.main_thread.start()

    def stop(self):
        self.is_active = False
        self.main_thread.join()
        # We need to call stop_recording here, after the main thread has stopped,
        # otherwise we might send data to the feeds that will not be recorded.
        if self.is_recording:
            self.stop_recording()
        self.source.stop()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

    def start_recording(self, path, recorder=None, **metadata):
        path = Path(path)
        Session.create_session(path, self, metadata)

        if recorder is None:
            if isinstance(self.source, MicSource):
                recorder = WavFileRecorder(
                    (path / "raw_data.wav").as_posix(), self.source.sample_rate, self.source.n_channels,
                    self.source.sample_width
                )
            else:
                recorder = PickleRecorder(path / "raw_data.pickle")
        self.recorder = recorder
        self.is_recording = True

    def stop_recording(self):
        self.recorder.stop()
        self.recorder = None
        self.is_recording = False

    def _read(self):
        """
        Return all new data points received since the last call to read()
        """
        data = self.source.read()
        if self.is_recording:
            self.recorder.write(data)
        if len(data) > 0:
            data = compute_signal_functions(data, self.functions)
        return data

    def add_derived_signal(self, signal):
        self.functions.append(signal)
