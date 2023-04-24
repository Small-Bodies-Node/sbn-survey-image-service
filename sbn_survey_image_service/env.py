"""SSOT FOR ENV VARIABLES"""

# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import inspect
import multiprocessing
from typing import List, Union
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True, verbose=True)

__all__: List[str] = ["ENV", "env_example"]


class SBNSISEnvironment:
    """Defines environment variables and their defaults.

    To add new variables, edit this class and `env_example`.

    """

    # Logging
    SBNSIS_LOG_FILE: str = os.path.abspath("./logging/sbnsis.log")

    # Data parameters
    TEST_DATA_PATH: str = os.path.abspath("./data/test")
    SBNSIS_CUTOUT_CACHE: str = "/tmp"
    MAXIMUM_CUTOUT_SIZE: int = 1024

    # PDS API access point
    PDS_REGISTRY: str = "https://pds.nasa.gov/api/search/1.0/"

    # Deployment parameters
    DEPLOYMENT: str = "AWS"

    # Gunicorn parameters
    LIVE_GUNICORN_INSTANCES: int = -1
    APP_NAME: str = "sbnsis-service"
    API_PORT: int = 5000
    BASE_HREF: str = "/"
    IS_DAEMON: str = "TRUE"

    def __init__(self):
        key: str
        value: Union[str, int, None]
        for key, value in inspect.getmembers(SBNSISEnvironment):
            if key.startswith("_"):
                continue

            value = os.getenv(key)
            if value is not None:
                value_type = type(getattr(self, key))
                setattr(self, key, value_type(value))

        if self.LIVE_GUNICORN_INSTANCES < 0:
            self.LIVE_GUNICORN_INSTANCES = multiprocessing.cpu_count() * 2


ENV: SBNSISEnvironment = SBNSISEnvironment()


env_example: str = f"""
# sbnsis configuration

################
# Edit to suit #
################

# Location of this instance: remote, AWS, or UMD
DEPLOYMENT={SBNSISEnvironment.DEPLOYMENT}

PDS_REGISTRY={SBNSISEnvironment.PDS_REGISTRY}

# Local cache location for served data
SBNSIS_CUTOUT_CACHE={SBNSISEnvironment.SBNSIS_CUTOUT_CACHE}

################################
# Editing generally not needed #
################################

# API CONFIG
APP_NAME={SBNSISEnvironment.APP_NAME}
API_PORT={SBNSISEnvironment.API_PORT}
BASE_HREF={SBNSISEnvironment.BASE_HREF}

# QUERY CONFIG
# none

# Cutout CONFIG
MAXIMUM_CUTOUT_SIZE={SBNSISEnvironment.MAXIMUM_CUTOUT_SIZE}

# Gunicorn settings
# if LIVE_GUNICORN_INSTANCES==-1 then it's determined by CPU count
LIVE_GUNICORN_INSTANCES={SBNSISEnvironment.LIVE_GUNICORN_INSTANCES}

# local file path for generated test data set
TEST_DATA_PATH={SBNSISEnvironment.TEST_DATA_PATH}

# log file
# _sbnsis will rotate any files matching "*.log" in the ./logging directory
SBNSIS_LOG_FILE={SBNSISEnvironment.SBNSIS_LOG_FILE}
""".strip()


# Debugging block
# print("=========================")
# print(ENV.LIVE_GUNICORN_INSTANCES)
# print(ENV.LIVE_WORKER_INSTANCES)
# print(ENV.DEPLOYMENT_TIER)
# print(ENV.DB_DATABASE)
# print(ENV.DB_PASSWORD)
# print(ENV.DB_USERNAME)
# print()
# print(ENV.CATCH_LOG)
# print(ENV.CATCH_ARCHIVE_PATH)
# print(ENV.CATCH_CUTOUT_PATH)
# print(ENV.CATCH_THUMBNAIL_PATH)
# print(ENV.IS_DAEMON)
# print("=========================")
