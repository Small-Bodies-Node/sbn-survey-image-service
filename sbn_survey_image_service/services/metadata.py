# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Data product metdata service."""

__all__ = ["metadata_query", "metadata_summary"]

from urllib.parse import quote
from typing import Any, List, Tuple
from .database_provider import data_provider_session, Session
from ..models.image import Image
from ..config.env import ENV


def metadata_query(
    collection: str | None = None,
    facility: str | None = None,
    instrument: str | None = None,
    dptype: str | None = None,
    format: str = "fits",
    maxrec: int = 100,
    offset: int = 0,
) -> Tuple[int, List[dict]]:
    """Query database for image metadata.


    Returns
    -------
    count : int
        Total number of matches.

    matches : list of dict
        The matches.

    """

    matches: List[dict] = []

    session: Session
    with data_provider_session() as session:
        query: Any = session.query(Image)
        if collection is not None:
            query = query.filter(Image.collection == collection)
        if facility is not None:
            query = query.filter(Image.facility == facility)
        if instrument is not None:
            query = query.filter(Image.instrument == instrument)
        if dptype is not None:
            query = query.filter(Image.data_product_type == dptype)

        count: int = query.count()

        if maxrec is not None:
            query = query.limit(maxrec)

        query = query.offset(offset)

        images: List[Image] = query.all()

        url_base: str = ENV.PUBLIC_URL
        if ENV.IS_PRODUCTION.upper() != "TRUE":
            url_base = f"http://{ENV.API_HOST}:{ENV.API_PORT}/{ENV.BASE_HREF.lstrip('/')}".rstrip(
                "/"
            )

        for im in images:
            matches.append(
                {
                    "obs_id": im.obs_id,
                    "collection": im.collection,
                    "facility": im.facility,
                    "instrument": im.instrument,
                    "dptype": im.data_product_type,
                    "calibration_level": im.calibration_level,
                    "target": im.target,
                    "pixel_scale": im.pixel_scale,
                    "access_url": f"{url_base}/images/{quote(im.obs_id)}?format={format}",
                }
            )

    return count, matches


def metadata_summary() -> List[dict]:
    """Summarize the database holdings.


    Returns
    -------
    summary : list of dict

    """

    session: Session
    summary: List[dict] = []
    with data_provider_session() as session:
        rows: List[dict] = (
            session.query(Image.collection, Image.facility, Image.instrument)
            .distinct()
            .all()
        )

        for collection, facility, instrument in rows:
            count: int = (
                session.query(Image)
                .filter(Image.collection == collection)
                .filter(Image.facility == facility)
                .filter(Image.instrument == instrument)
            ).count()
            summary.append(
                {
                    "collection": collection,
                    "facility": facility,
                    "instrument": instrument,
                    "count": count,
                }
            )

    return summary
