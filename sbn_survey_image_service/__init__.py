# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""SBN Survey Image Service"""

import os
from importlib.metadata import version as _version, PackageNotFoundError

# make cache directory set umask
from .config import exceptions
from .config import env

try:
    __version__ = _version(__name__)
except PackageNotFoundError:
    pass

os.system(f"mkdir -p {env.ENV.SBNSIS_CUTOUT_CACHE}")
del os, PackageNotFoundError, _version
