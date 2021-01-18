# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""SBN Survey Image Service data models.

Image: ORM Model for table of served image data products.

"""

import typing
from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base

Base: typing.Any = declarative_base()


class Image(Base):
    """ ORM Class for served image data products"""

    __tablename__ = 'image'

    image_id = Column(String, primary_key=True)
    """
        PDS3 product ID or PDS4 LID (i.e.,
        Product_Observational/Identification_Area/logical_identifier).
        Unique within the database.
    """

    image_path = Column(String)
    """
        The local path to the data product.
    """

    label_path = Column(String)
    """
        The local path to the data product label.
    """

    def __repr__(self) -> str:
        return f"Image(product_id='{self.product_id}', path='{self.path}')"

    def __str__(self) -> str:
        return f"<Class Image: {self.product_id}, {self.path}>"
