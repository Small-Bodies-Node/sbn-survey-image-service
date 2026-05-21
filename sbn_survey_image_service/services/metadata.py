# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Data product metdata service."""

__all__ = ["metadata_query", "metadata_summary"]

from urllib.parse import quote
from typing import Any
from astropy.time import Time
from .database_provider import data_provider_session, Session
from ..models.image import Image
from ..config.env import ENV


def metadata_query(
    collection: str | None = None,
    facility: str | None = None,
    instrument: str | None = None,
    dptype: str | None = None,
    after: str | None = None,
    before: str | None = None,
    format: str = "fits",
    maxrec: int = 100,
    offset: int = 0,
) -> tuple[int, list[dict]]:
    """Query database for image metadata.


    Returns
    -------
    count : int
        Total number of matches.

    matches : list of dict
        The matches.

    """

    matches: list[dict] = []

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
        if after is not None:
            query = query.filter(Image.date > Time(after).iso)
        if before is not None:
            query = query.filter(Image.date < Time(before).iso)

        count: int = query.count()

        if maxrec is not None:
            query = query.limit(maxrec)

        query = query.offset(offset)

        images: list[Image] = query.all()

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
                    "date": im.date,
                    "access_url": f"{url_base}/images/{quote(im.obs_id)}?format={format}",
                }
            )

    return count, matches


def metadata_summary() -> list[dict]:
    """Summarize the database holdings.


    Returns
    -------
    summary : list of dict

    """

    session: Session
    summary: list[dict] = []
    with data_provider_session() as session:
        rows: list[dict] = (
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
