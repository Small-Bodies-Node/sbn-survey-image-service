# Licensed under a 3-clause BSD style license - see LICENSE.rst

import json
import uuid
import logging
from typing import List

from ..config.logging import get_logger
from ..services.metadata import metadata_summary


def get_summary() -> List[dict]:
    """Controller for summaries."""

    logger: logging.Logger = get_logger()
    job_id: uuid.UUID = uuid.uuid4()
    logger.info(json.dumps({"job_id": job_id.hex}))

    summary: List[dict] = metadata_summary()

    return summary
