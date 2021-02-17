# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Entry point to Flask-Connexion API
"""

import os
import uuid
import json
import logging
from typing import Any, Dict, Optional
from connexion import FlaskApp
from flask import send_file, Response
from flask_cors import CORS
from ..env import ENV
from ..services import label_query, image_query, database_provider
from ..logging import get_logger
from ..exceptions import SBNSISException

MIME_TYPES = {
    '.xml': 'text/xml',
    '.fit': 'image/fits',
    '.fits': 'image/fits',
    '.fit.fz': 'image/fits',
    '.fits.fz': 'image/fits',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png'
}


def get_image(id: str, ra: Optional[float] = None, dec: Optional[float] = None,
              size: Optional[str] = None, format: str = 'fits',
              download: bool = False) -> Response:
    """Controller for survey image service."""

    logger: logging.Logger = get_logger()
    job_id: uuid.UUID = uuid.uuid4()
    logger.info(json.dumps({
        'job_id': job_id.hex, 'id': id, 'ra': ra, 'dec': dec, 'size': size, 'format': format,
        'download': download
    }))

    filename: str
    attachment_filename: str
    if format.lower() == 'label':
        filename, attachment_filename = label_query(id)
    else:
        filename, attachment_filename = image_query(
            id, ra=ra, dec=dec, size=size, format=format)

    mime_type: str = MIME_TYPES.get(
        os.path.splitext(attachment_filename.lower())[1],
        'text/plain')

    logger.info(json.dumps({
        'job_id': job_id.hex,
        'filename': filename,
        'attachment_filename': attachment_filename,
        'mime_type': mime_type
    }))

    return send_file(filename, mimetype=mime_type,
                     as_attachment=download,
                     attachment_filename=attachment_filename)


###########################################
# BEGIN API
###########################################


app = FlaskApp(__name__, options={})
app.add_api('openapi.yaml', base_path=ENV.BASE_HREF)
CORS(app.app)
application = app.app


@application.teardown_appcontext
def shutdown_session(exception: Exception = None) -> None:
    """ Boilerplate connexion code """
    database_provider.db_session.remove()


@application.errorhandler(SBNSISException)
def handle_sbnsis_error(error: Exception):
    """Log errors."""
    get_logger().exception('SBS Survey Image Service error.')
    return str(error), getattr(error, 'code', 500)


@application.errorhandler(Exception)
def handle_other_error(error: Exception):
    """Log errors."""
    get_logger().exception('An error occurred.')
    return ('Unexpected error.  Please report if the problem persists.',
            getattr(error, 'code', 500))


if __name__ == '__main__':
    app.run(port=ENV.API_PORT, use_reloader=False, threaded=False)
