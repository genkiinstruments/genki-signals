"""
Signal functions are functions of signals that generate other signals.
They are assumed to be pure functions, i.e. they are deterministic
and have no side effects. This means they can be serialized and
deserialized, and their parameters can be treated like hyperparameters
in a machine learning model. When a data session is recorded with a signal
system, only the json serialisation of the signal functions is stored.
Signal functions are also assumed to be causal, i.e. they only depend
on past values of the input and can thus be computed in real time.
"""

from .arithmetic import *  # noqa: F401, F403
from .filters import *  # noqa: F401, F403
from .geometry import *  # noqa: F401, F403
from .inference import *  # noqa: F401, F403
from .windowed import *  # noqa: F401, F403
from .shape import *  # noqa: F401, F403
from .waveforms import *  # noqa: F401, F403
from .base import compute_signal_functions, SignalFunction, SignalName  # noqa: F401, F403
