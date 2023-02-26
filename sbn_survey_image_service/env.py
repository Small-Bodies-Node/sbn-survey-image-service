"""SSOT FOR ENV VARIABLES"""

# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import inspect
import multiprocessing
from typing import List, Union
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True, verbose=True)

__all__: List[str] = ["ENV", "env_example"]


class SBNSISEnvironment():
    """Defines environment variables and their defaults.

    To add new variables, edit this class and `env_example`.

    """

    # Logging
    SBNSIS_LOG_FILE: str = os.path.abspath('./logging/sbnsis.log')

    # Data parameters
    TEST_DATA_PATH: str = os.path.abspath("./data/test")
    SBNSIS_CUTOUT_CACHE: str = "/tmp"
    MAXIMUM_CUTOUT_SIZE: int = 1024

    # Database parameters
    DB_HOST: str = ""
    DB_DIALECT: str = "sqlite"
    DB_USERNAME: str = ""
    DB_PASSWORD: str = ""
    DB_DATABASE: str = os.path.abspath("default.db")

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

# DB CONFIG
#
# Example sqlite database:
#   DB_DIALECT=sqlite
#   DB_DATABASE=sbnsis.db
# 
# Example postgresql database:
#   DB_DIALECT=postgresql+psycopg2
#   DB_HOST=localhost
#   Leave DB_HOST blank to use a UNIX socket.
#   Define as needed: DB_USERNAME, DB_PASSWORD, DB_DATABASE
#

DB_DIALECT={SBNSISEnvironment.DB_DIALECT}
DB_HOST={SBNSISEnvironment.DB_HOST}
# DB_USERNAME=username
# DB_PASSWORD=password
DB_DATABASE={SBNSISEnvironment.DB_DATABASE}

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
