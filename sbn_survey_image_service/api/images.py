# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
import json
import uuid
import logging

from flask import send_file, Response

from ..config import MIME_TYPES
from ..config.logging import get_logger
from ..services.label import label_query
from ..services.image import image_query


def get_image(
    id: str,
    ra: float | None = None,
    dec: float | None = None,
    size: str | None = None,
    format: str = "fits",
    download: bool = False,
) -> Response:
    """Controller for survey image service."""

    logger: logging.Logger = get_logger()
    job_id: uuid.UUID = uuid.uuid4()
    logger.info(
        json.dumps(
            {
                "job_id": job_id.hex,
                "job": "images",
                "id": id,
                "ra": ra,
                "dec": dec,
                "size": size,
                "format": format,
                "download": download,
            }
        )
    )

    filename: str
    download_filename: str
    if format.lower() == "label":
        filename, download_filename = label_query(id)
    else:
        filename, download_filename = image_query(
            id, ra=ra, dec=dec, size=size, format=format
        )

    mime_type: str = MIME_TYPES.get(
        os.path.splitext(download_filename.lower())[1], "text/plain"
    )

    logger.info(
        json.dumps(
            {
                "job_id": job_id.hex,
                "job": "images",
                "filename": filename,
                "download_filename": download_filename,
                "mime_type": mime_type,
            }
        )
    )

    return send_file(
        filename,
        mimetype=mime_type,
        as_attachment=download,
        download_name=download_filename,
    )
