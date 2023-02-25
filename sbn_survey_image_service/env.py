"""SSOT FOR ENV VARIABLES"""

# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
from typing import Optional, List
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True, verbose=True)

__all__: List[str] = ["ENV", "env_example"]

class ENV():
    """Class to store all env variables used in app.
    
    When new variables are added, also edit `env_example` below.

    """

    # String properties
    TEST_DATA_PATH: str = os.path.abspath(str(
        os.getenv("TEST_DATA_PATH", "./data/test")))
    DB_HOST: str = str(os.getenv("DB_HOST", ""))
    DB_DIALECT: str = str(os.getenv("DB_DIALECT", "sqlite"))
    DB_USERNAME: str = str(os.getenv("DB_USERNAME", ""))
    DB_PASSWORD: str = str(os.getenv("DB_PASSWORD", ""))
    DB_DATABASE: str = str(os.getenv("DB_DATABASE", os.path.abspath("default.db")))
    BASE_HREF: str = str(os.getenv("BASE_HREF", "/"))
    SBNSIS_CUTOUT_CACHE: str = str(os.getenv("SBNSIS_CUTOUT_CACHE", "/tmp"))
    MAXIMUM_CUTOUT_SIZE: int = int(os.getenv("MAXIMUM_CUTOUT_SIZE", 1024))
    SBNSIS_LOG_FILE: str = str(os.path.abspath(
        os.getenv('SBNSIS_LOG_FILE', os.path.abspath('./logging/sbnsis.log'))))

    # Numeric properties
    LIVE_GUNICORN_INSTANCES: int = int(
        os.getenv("LIVE_GUNICORN_INSTANCES", -1))
    API_PORT: int = int(
        os.getenv("API_PORT", 5000))

    # Boolean Properties
    IS_DAEMON: bool = os.getenv("IS_DAEMON") == 'TRUE'


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

DB_DIALECT=postgresql+psycopg2
DB_HOST=
# DB_USERNAME=username
# DB_PASSWORD=password
DB_DATABASE=sbnsis

# Local cache location for served data
SBNSIS_CUTOUT_CACHE={ENV.SBNSIS_CUTOUT_CACHE}

################################
# Editing generally not needed #
################################

# API CONFIG
API_PORT={ENV.API_PORT}
BASE_HREF={ENV.BASE_HREF}

# QUERY CONFIG
# none

# Cutout CONFIG
MAXIMUM_CUTOUT_SIZE={ENV.MAXIMUM_CUTOUT_SIZE}

# Gunicorn settings
# if LIVE_GUNICORN_INSTANCES==-1 then it's determined by CPU count
LIVE_GUNICORN_INSTANCES={ENV.LIVE_GUNICORN_INSTANCES}

# local file path for generated test data set
TEST_DATA_PATH={ENV.TEST_DATA_PATH}

# log file
SBNSIS_LOG_FILE={ENV.SBNSIS_LOG_FILE}
"""


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
