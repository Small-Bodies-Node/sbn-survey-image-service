# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Data product label service."""

__all__ = [
    'label_query'
]

from sqlalchemy.orm.exc import NoResultFound
from .database_provider import data_provider_session, Session
from ..models import Image
from ..exceptions import InvalidImageID


def label_query(image_id: str) -> str:
    """Query database for data product label file name."""
    session: Session
    with data_provider_session() as session:
        exc: Exception
        try:
            q: str = session.query(Image.label_path).filter(
                Image.image_id == image_id).one()[0]
        except NoResultFound as exc:
            raise InvalidImageID from exc

    return q
