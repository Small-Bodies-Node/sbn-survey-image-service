# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Entry point to Flask-Connexion API
"""

import logging

import connexion
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware

from . import __version__ as version
from .config.logging import get_logger
from .config.env import ENV
from .config.exceptions import SBNSISException
from .services.database_provider import db_session

logger: logging.Logger = get_logger()
app = connexion.FlaskApp(__name__, specification_dir="api/")

app.add_middleware(
    CORSMiddleware,
    position=MiddlewarePosition.BEFORE_EXCEPTION,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_api(
    "openapi.yaml",
    arguments={
        "version": str(version),
        "base_href": ENV.BASE_HREF,
    },
)
application = app.app


@application.teardown_appcontext
def shutdown_db_session(exception: Exception = None) -> None:
    db_session.remove()


@application.errorhandler(SBNSISException)
def handle_sbnsis_error(error: Exception):
    """Log errors.

    The HTTP status code is based on the exception, or 500 if it is not defined.

    """

    get_logger().exception("SBS Survey Image Service error.")
    return str(error), getattr(error, "code", 500)


@application.errorhandler(Exception)
def handle_other_error(error: Exception):
    """Log errors."""

    get_logger().exception("An error occurred.")
    return (
        "Unexpected error.  Please report if the problem persists.",
        getattr(error, "code", 500),
    )


if __name__ == "__main__":
    # for development
    logger.info("Running " + ENV.APP_NAME)
    logger.info(application.url_map)
    app.run("sbn_survey_image_service.app:app", host=ENV.API_HOST, port=ENV.API_PORT)
