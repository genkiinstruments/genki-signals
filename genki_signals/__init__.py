from .frontends import *  # noqa: F401, F403
from .functions import *  # noqa: F401, F403
from .sources import *  # noqa: F401, F403

from .dead_reckoning import *  # noqa: F401, F403
from .filters import *  # noqa: F401, F403
from .fusion import *  # noqa: F401, F403
from .recorders import *  # noqa: F401, F403
from .session import *  # noqa: F401, F403
from .system import *  # noqa: F401, F403

from .buffers import Buffer, DataBuffer  # noqa: F401

__version__ = "0.1.1"

__doc__ = """
genki_signals
=============

Description
-----------
Genki Signals is a library for processing and manipulating time series data.

Example notebooks can be found on the `GitHub repo <https://github.com/genkiinstruments/genki-signals>`.
"""
