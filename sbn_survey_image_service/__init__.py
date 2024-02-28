# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""SBN Survey Image Service"""

import os
from importlib.metadata import version as _version, PackageNotFoundError

# make cache directory set umask
from . import exceptions
from . import env
from . import services
from . import models

try:
    __version__ = _version(__name__)
except PackageNotFoundError:
    pass

os.system(f"mkdir -p {env.ENV.SBNSIS_CUTOUT_CACHE}")
del os, PackageNotFoundError, _version
