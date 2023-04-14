import logging

from genki_signals.buffers import DataBuffer

logger = logging.getLogger(__name__)


class System:
    """
    A System is a DataSource with a list of derived signals. The system
    collects data points as they arrive from the source, and computes derived signals.
    """

    def __init__(self, data_source, derived_signals=None):
        self.source = data_source
        if derived_signals is None:
            derived_signals = []
        self.derived_signals = derived_signals
        self.is_active = False

    def start(self):
        self.is_active = True
        self.source.start()

    def stop(self):
        self.source.stop()
        self.is_active = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

    def _compute_derived(self, data: DataBuffer):
        for signal in self.derived_signals:
            inputs = tuple(data[name] for name in signal.input_signals)

            # TODO: error reporting here? Remove ill-behaved signals?
            #       * If the signal throws an exception, this context is useful
            try:
                output = signal(*inputs)
                data[signal.name] = output
            except Exception as e:
                logger.exception(f"Error computing derived signal {signal.name}")
                raise e

    def read(self):
        """
        Return all new data points received since the last call to read()
        """
        data = self.source.read()
        if len(data) > 0:
            self._compute_derived(data)
        return data

    def add_derived_signal(self, signal):
        self.derived_signals.append(signal)
