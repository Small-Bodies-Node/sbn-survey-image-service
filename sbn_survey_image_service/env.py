"""SSOT FOR ENV VARIABLES"""

# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
from typing import Optional
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True, verbose=True)


class ENV():
    """ Class to store all env variables used in app """

    # String properties
    TEST_DATA_PATH: str = os.path.abspath(str(
        os.getenv("TEST_DATA_PATH", "./data/test")))
    DB_HOST: str = str(os.getenv("DB_HOST", ""))
    DB_DIALECT: str = str(os.getenv("DB_DIALECT", "sqlite"))
    DB_USERNAME: str = str(os.getenv("DB_USERNAME", ""))
    DB_PASSWORD: str = str(os.getenv("DB_PASSWORD", ""))
    DB_DATABASE: str = str(os.getenv("DB_DATABASE", "default.db"))
    BASE_HREF: str = str(os.getenv("BASE_HREF", "/"))
    SBNSIS_CUTOUT_CACHE: str = str(os.getenv("SBNSIS_CUTOUT_CACHE", "/tmp"))

    # Numeric properties
    LIVE_GUNICORN_INSTANCES: int = int(
        os.getenv("LIVE_GUNICORN_INSTANCES", -1))
    API_PORT: int = int(
        os.getenv("API_PORT", 5004))
    MAX_RESULTS: int = int(
        os.getenv("MAX_RESULTS", 15))

    # Boolean Properties
    IS_DAEMON: bool = os.getenv("IS_DAEMON") == 'TRUE'


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
