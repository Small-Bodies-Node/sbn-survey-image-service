"""SSOT FOR ENV VARIABLES"""

# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import sys
import inspect
import multiprocessing
from dotenv import load_dotenv, find_dotenv

__all__ = ["ENV", "env_format"]

try:
    dotenv_file = find_dotenv(raise_error_if_not_found=True, usecwd=True)
    sys.stderr.write(f"Reading {dotenv_file}\n")
    load_dotenv(dotenv_file, override=True, verbose=True)
    env_configured = True
except IOError:
    env_configured = False


class SBNSISEnvironment:
    """Defines environment variables and their defaults.

    To add new variables, edit this class and `env_format`.

    """

    # Logging
    SBNSIS_LOG_FILE: str = os.path.abspath("./logging/sbnsis.log")

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
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 5000
    BASE_HREF: str = "/"
    PUBLIC_URL: str = "https://sbnsurveys.astro.umd.edu/api"
    IS_DAEMON: str = "TRUE"
    IS_PRODUCTION: str = "FALSE"

    def __init__(self):
        key: str
        value: str | int | None
        for key, value in inspect.getmembers(SBNSISEnvironment):
            if key.startswith("_"):
                continue

            value = os.getenv(key)
            if value is not None:
                value_type = type(getattr(self, key))
                setattr(self, key, value_type(value))

        if self.LIVE_GUNICORN_INSTANCES < 0:
            self.LIVE_GUNICORN_INSTANCES = multiprocessing.cpu_count() * 2

    def is_configured(self) -> bool:
        """Returns True if the .env file was successfully found."""
        return env_configured


ENV = SBNSISEnvironment()


env_format = """
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

DB_DIALECT={env.DB_DIALECT}
DB_HOST={env.DB_HOST}
# DB_USERNAME=username
# DB_PASSWORD=password
DB_DATABASE={env.DB_DATABASE}

# Local cache location for served data
SBNSIS_CUTOUT_CACHE={env.SBNSIS_CUTOUT_CACHE}

################################
# Editing generally not needed #
################################

# API CONFIG
APP_NAME={env.APP_NAME}
API_HOST={env.API_HOST}
API_PORT={env.API_PORT}
BASE_HREF={env.BASE_HREF}

# URL used in production
PUBLIC_URL=https://sbnsurveys.astro.umd.edu/api

# QUERY CONFIG
# none

# Cutout CONFIG
MAXIMUM_CUTOUT_SIZE={env.MAXIMUM_CUTOUT_SIZE}

# Gunicorn settings
# if LIVE_GUNICORN_INSTANCES==-1 then it's determined by CPU count
LIVE_GUNICORN_INSTANCES={env.LIVE_GUNICORN_INSTANCES}

# local file path for generated test data set
TEST_DATA_PATH={env.TEST_DATA_PATH}

# log file
# sbnsis will rotate any files matching "*.log" in the ./logging directory
SBNSIS_LOG_FILE={env.SBNSIS_LOG_FILE}
""".strip()
