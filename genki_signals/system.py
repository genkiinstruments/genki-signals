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
        self.running = False

    def start(self):
        self.running = True
        self.source.start()

    def stop(self):
        self.source.stop()
        self.running = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

    def _compute_derived(self, data: DataBuffer):
        for signal in self.derived_signals:
            inputs = tuple(data[name] for name in signal.input_names)

            # TODO: error reporting here? Remove ill-behaved signals?
            #       * If the signal throws an exception, this context is useful
            #       * the output should have the same length as the input
            output = signal(*inputs)
            assert output.shape[-1] == len(data), f"Expected output of length {len(data)=}, got {output.shape[-1]=}"
            data[signal.name] = output

    def read(self):
        """
        Return all new data points received since the last call to read()
        """
        data = self.source.read()
        if len(data) > 0:
            self._compute_derived(data)
        return data
