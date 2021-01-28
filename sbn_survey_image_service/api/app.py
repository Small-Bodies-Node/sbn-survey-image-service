# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Entry point to Flask-Connexion API
"""

import os
from typing import Optional
from connexion import FlaskApp
from flask import send_file, Response
from flask_cors import CORS
from ..env import ENV
from ..services import label_query, image_query, database_provider

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
    filename: str
    if format.lower() == 'label':
        filename = label_query(id)
    else:
        filename = image_query(id, ra=ra, dec=dec, size=size, format=format)

    mime_type: str = MIME_TYPES.get(
        os.path.splitext(filename.lower())[1],
        'text/plain')

    return send_file(filename, mimetype=mime_type,
                     as_attachment=download)


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


if __name__ == '__main__':
    app.run(port=ENV.API_PORT, use_reloader=False, threaded=False)
