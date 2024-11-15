# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""SBN Survey Image Service data models.

Image: ORM model for a metadata harvesting log.

"""

from sqlalchemy import Column, String, Integer
from .base import Base


class HarvestLog(Base):
    """ORM class for metadata harvesting log."""

    __tablename__ = "harvest_log"

    id: int = Column(Integer, primary_key=True)

    start: str = Column(String, nullable=False, index=True)
    """Date and time the harvesting started (UTC)."""

    end: str = Column(String, nullable=False, index=True)
    """Date and time the harvesting ended (UTC)."""

    source: str = Column(String, nullable=False)
    """Data source being harvested."""

    time_of_last: str = Column(String, nullable=False)
    """Time stamp of the last file added.
    
    This is intended to be used as the basis for discovering what new data could
    be added from external archives.
    
    """

    files: int = Column(Integer, nullable=False)
    """Number of files harvested."""

    added: int = Column(Integer, nullable=False)
    """Number of files added to the database."""

    errors: int = Column(Integer, nullable=False)
    """Number of files that errored."""
