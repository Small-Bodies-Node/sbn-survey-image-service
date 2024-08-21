# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Survey image service logging.

"""

import os
import pathlib
import logging
from .env import ENV


def setup() -> logging.Logger:
    """Set up logging.

    The logger instance is named 'SBN Survey Image Service' and may be
    returned with ``get_logger``.


    Returns
    -------
    logger : logging.Logger

    """

    logger: logging.Logger = logging.getLogger("SBN Survey Image Service")

    logger.handlers = []

    logger.setLevel(logging.INFO)

    # delete any previous handlers
    logger.handlers = []

    formatter: logging.Formatter = logging.Formatter(
        "%(levelname)s:%(name)s:%(asctime)s: %(message)s"
    )

    console: logging.StreamHandler = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    logfile: logging.FileHandler = logging.FileHandler(ENV.SBNSIS_LOG_FILE)
    logfile.setFormatter(formatter)
    logger.addHandler(logfile)

    # create log file if it does not exist
    if not os.path.exists(ENV.SBNSIS_LOG_FILE):
        pathlib.Path(ENV.SBNSIS_LOG_FILE).touch(mode=0o640)

    handler: logging.Handler
    for handler in logger.handlers:
        if hasattr(handler, "baseFilename"):
            logger.info("Logging to %s", handler.baseFilename)

    return logger


def get_logger() -> logging.Logger:
    """Return the logger.

    This is a convenience function that will call ``setup``, as needed.


    Returns
    -------
    logger : logging.Logger

    """

    logger: logging.Logger = logging.getLogger("SBN Survey Image Service")

    if len(logger.handlers) == 0:
        setup()

    return logger
