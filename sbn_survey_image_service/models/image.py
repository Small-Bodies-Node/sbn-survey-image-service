# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""SBN Survey Image Service data models.

Image: ORM Model for table of served image data products.

"""

from sqlalchemy import Column, String, Integer
from . import Base


class Image(Base):
    """ORM Class for served image data products.

    IVOA ObsCore model: https://ivoa.net/documents/ObsCore/20170509/REC-ObsCore-v1.1-20170509.pdf
    """

    __tablename__ = 'image'

    id: int = Column(Integer, primary_key=True)

    obs_id: str = Column(String, unique=True, nullable=False)
    """
        Unique data production ID
        
        PDS3: PRODUCT_ID
        PDS4: data product logical ID
        IVOA ObsCore: obs_id
    """

    collection: str = Column(String, nullable=False)
    """
        Data collection identifier.
        
        PDS3: DATA_SET_ID
        PDS4: data collection logical ID
        IVOA ObsCore: obs_collection.
    """

    facility: str = Column(String, nullable=False)
    """
        Observing facility name.
        
        PDS3: e.g., INSTRUMENT_HOST_NAME
        PDS4: e.g., Observing_System/Observing_System_Component/name
        IVOA ObsCore: facility_name
    """

    instrument: str = Column(String, nullable=False)
    """
        Observing instrument name.

        PDS3: INSTRUMENT_NAME
        PDS4: e.g., Observing_System/Observing_System_Component/name
        IVOA ObsCore: instrument_name
    """

    data_product_type: str = Column(String, default='image', nullable=False)
    """
        Data product type.

        Likely 'image' for all data.

        PDS3: ?
        PDS4: ?
        IVOA ObsCore: dataproduct_type
    """

    calibration_level: str = Column(String, nullable=True)
    """
        Data calibration level.

        PDS3: ?
        PDS4: ?
        IVOA ObsCore: calib_level
    """

    target: str = Column(String, nullable=True)
    """
        Intended target.

        PDS3: e.g., TARGET_NAME
        PDS4: Target_Identification/name
        IVOA ObsCore: target_name
    """

    image_path: str = Column(String, nullable=True)
    """
        The local path to the data product.
    """

    label_path: str = Column(String, nullable=True)
    """
        The local path to the data product label.
    """

    def __repr__(self) -> str:
        return f"Image(obs_id='{self.obs_id}', image_path='{self.image_path}', label_path='{self.label_path}')"

    def __str__(self) -> str:
        return f"<Class Image: {self.obs_id}>"
