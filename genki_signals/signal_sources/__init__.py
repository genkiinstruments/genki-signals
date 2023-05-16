"""
Signal sources are classes that sample signals from various sources, usually external devices.

Some signal sources act as "samplers" meaning they have their own clock and sample at a given rate.
Other sources are pure "sources" which means they can only generate data when asked to do so, and
need to be sampled by a sampler.
"""

from .sampler import Sampler  # noqa: F401, F403
from .generators import *  # noqa: F401, F403
from .wave import *  # noqa: F401, F403
from .local import *  # noqa: F401, F403
from .ble import *  # noqa: F401, F403
