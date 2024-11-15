# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Base ORM model."""

from typing import Any
from sqlalchemy.orm import declarative_base

Base: Any = declarative_base()
