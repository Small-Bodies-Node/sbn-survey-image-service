# Licensed under a 3-clause BSD style license - see LICENSE.rst

import json
import uuid
import logging
from typing import Dict, List

from ..config.logging import get_logger
from ..services.metadata import metadata_query


def run_query(
    collection: str | None = None,
    facility: str | None = None,
    instrument: str | None = None,
    dptype: str | None = None,
    format: str = "fits",
    maxrec: int = 100,
    offset: int = 0,
) -> Dict[str, int | List[dict]]:
    """Controller for metadata queries."""

    logger: logging.Logger = get_logger()
    job_id: uuid.UUID = uuid.uuid4()
    logger.info(
        json.dumps(
            {
                "job_id": job_id.hex,
                "job": "query",
                "collection": collection,
                "facility": facility,
                "instrument": instrument,
                "dptype": dptype,
                "format": format,
                "maxrec": maxrec,
                "offset": offset,
            }
        )
    )

    total, results = metadata_query(
        collection=collection,
        facility=facility,
        instrument=instrument,
        dptype=dptype,
        format=format,
        maxrec=maxrec,
        offset=offset,
    )

    return {"total": total, "offset": offset, "count": len(results), "results": results}
