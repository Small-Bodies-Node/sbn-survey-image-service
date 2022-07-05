# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""SBN Survey Image Service data models.

Image: ORM Model for table of served image data products.

"""

from sqlalchemy import Column, String, Integer
from sqlalchemy.sql.sqltypes import Float
from . import Base


class Image(Base):
    """ORM Class for served image data products.

    IVOA ObsCore model: https://ivoa.net/documents/ObsCore/20170509/REC-ObsCore-v1.1-20170509.pdf
    """

    __tablename__ = 'image'

    id: int = Column(Integer, primary_key=True)

    obs_id: str = Column(String, unique=True, nullable=False, index=True)
    """
        Unique data product ID
        
        PDS3: PRODUCT_ID
        PDS4: data product logical ID
        IVOA ObsCore: obs_id
    """

    collection: str = Column(String, nullable=False, index=True)
    """
        Data collection identifier.
        
        PDS3: DATA_SET_ID?
        PDS4: data bundle or collection logical ID (probably bundle)
        IVOA ObsCore: obs_collection.
    """

    facility: str = Column(String, nullable=False, index=True)
    """
        Observing facility name.
        
        PDS3: e.g., INSTRUMENT_HOST_NAME
        PDS4: e.g., Observing_System/Observing_System_Component/Internal_Reference/[reference_type='is_telescope']/../name
        IVOA ObsCore: facility_name
    """

    instrument: str = Column(String, nullable=False, index=True)
    """
        Observing instrument name.

        PDS3: INSTRUMENT_NAME
        PDS4: e.g., Observing_System/Observing_System_Component/Internal_Reference/[reference_type='is_instrument']/../name
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

    calibration_level: int = Column(Integer, nullable=True)
    """
        Data calibration level.

        PDS3: ?
        PDS4: Observation_Area/Primary_Result_Summary/processing_level
        IVOA ObsCore: calib_level
    """

    target: str = Column(String, nullable=True)
    """
        Intended target.

        PDS3: e.g., TARGET_NAME
        PDS4: Target_Identification/name
        IVOA ObsCore: target_name
    """

    pixel_scale: float = Column(Float(32), nullable=True)
    """
        Image pixel scale in degrees.
    """

    image_url: str = Column(String, nullable=True)
    """
        URL to the data product.
    """

    label_url: str = Column(String, nullable=True)
    """
        URL to the data product label.
    """

    def __repr__(self) -> str:
        return f"Image(obs_id='{self.obs_id}', image_url='{self.image_url}', label_url='{self.label_url}')"

    def __str__(self) -> str:
        return f"<Class Image: {self.obs_id}>"
