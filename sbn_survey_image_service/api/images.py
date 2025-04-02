# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
import json
import uuid

from flask import send_file, Response

from ..config import MIME_TYPES
from ..config.logging import get_logger
from ..config.exceptions import ParameterValueError
from ..services.label import label_query
from ..services.image import image_query


def get_image(
    id: str,
    ra: float | None = None,
    dec: float | None = None,
    size: str | None = None,
    align: bool = False,
    format: str = "fits",
    download: bool = False,
) -> Response:
    """Controller for survey image service."""

    logger = get_logger()
    job_id = uuid.uuid4()
    logger.info(
        json.dumps(
            {
                "job_id": job_id.hex,
                "job": "images",
                "id": id,
                "ra": ra,
                "dec": dec,
                "size": size,
                "align": align,
                "format": format,
                "download": download,
            }
        )
    )

    # Either define all, or none
    cutout_params_exist = [p is not None for p in (ra, dec, size)]
    if not all(cutout_params_exist) and any(cutout_params_exist):
        raise ParameterValueError(
            "If one of ra, dec, or size is defined, then all must be defined."
        )

    if align and not any(cutout_params_exist):
        raise ParameterValueError(
            "align=true is only allowed for cutouts."
        )

    align_requires = ["jpeg", "png"]
    if align and format.lower() not in align_requires:
        raise ParameterValueError(
            f"align=true requires format={', '.join(align_requires)}"
        )

    if format.lower() == "label":
        filename, download_filename = label_query(id)
    else:
        filename, download_filename = image_query(
            id, ra=ra, dec=dec, size=size, align=align, format=format
        )

    mime_type = MIME_TYPES.get(
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
