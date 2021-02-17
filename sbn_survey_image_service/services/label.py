# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Data product label service."""

__all__ = [
    'label_query'
]

import os
from typing import Tuple

from sqlalchemy.orm.exc import NoResultFound

from .database_provider import data_provider_session, Session
from ..models.image import Image
from ..exceptions import InvalidImageID
from ..data import url_to_local_file


def label_query(obs_id: str) -> Tuple[str, str]:
    """Query database for data product label file name."""
    session: Session
    with data_provider_session() as session:
        exc: Exception
        try:
            label_url: str = (
                session.query(Image.label_url)
                .filter(Image.obs_id == obs_id)
                .one()[0]
            )
        except NoResultFound as exc:
            raise InvalidImageID('Image ID not found in database.') from exc

    return url_to_local_file(label_url), os.path.basename(label_url)
