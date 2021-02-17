# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Data product image service."""

__all__ = [
    'image_query'
]

import os
from sbn_survey_image_service.data.core import url_to_local_file
from tempfile import mkstemp
from typing import List, Optional, Tuple
from subprocess import check_output

from sqlalchemy.orm.exc import NoResultFound
import astropy.units as u

from .database_provider import data_provider_session, Session
from ..data import url_to_local_file
from ..models.image import Image
from ..exceptions import InvalidImageID
from ..env import ENV

FORMATS = {
    'png': '--png',
    'jpeg': '--jpg'
}

# make cutout cache directory, as needed
os.system(f'mkdir -p {ENV.SBNSIS_CUTOUT_CACHE}')


def image_query(obs_id: str, ra: Optional[float] = None,
                dec: Optional[float] = None, size: Optional[str] = None,
                format: str = 'fits') -> Tuple[str, str]:
    """Query database for image file or cutout thereof.


    Parameters
    ----------
    obs_id : str
        PDS3 product ID or PDS4 logical identifier (LID).

    ra, dec : float, optional
        Extract sub-frame around this position: J2000 right ascension and
        declination in degrees.

    size : str, optional
        Sub-frame size in angular units, e.g., '5arcmin'.  Parsed with
        `astropy.units.Quantity`.

    format : str, optional
        Returned image format: fits, png, jpeg


    Returns
    -------
    image_path : str
        Path to requested image.

    attachment_filename : str
        Suggested filename for downloads.

    """

    if format not in ['fits', 'png', 'jpeg']:
        raise ValueError('image_query format must be fits, png, or jpeg.')

    session: Session
    with data_provider_session() as session:
        exc: Exception
        try:
            im: Image = session.query(Image).filter(
                Image.obs_id == obs_id).one()
        except NoResultFound as exc:
            raise InvalidImageID from exc

        session.expunge(im)

    source_image_path: str = url_to_local_file(im.image_url)
    source_label_path: str = url_to_local_file(im.label_url)

    cmd: List[str] = ['fitscut', '-f']

    if FORMATS.get(format) is not None:
        cmd.extend([str(FORMATS.get(format)),
                    # '--asinh-scale'
                    '--autoscale=1'
                    ])

    suffix: str = ''
    if (ra is None) or (dec is None) or (size is None):
        if format == 'fits':
            # full-frame fits image, we're done
            return url_to_local_file(im.image_url), os.path.basename(im.image_url)

        # otherwise return full-frame jpeg or png
        cmd.append('--all')
    else:
        # append cutout arguments

        # RA 0 to 360
        ra = ra % 360

        # Dec -90 to 90
        dec = min(max(dec, -90), 90)

        # cutout size 1 to ENV.MAXIMUM_CUTOUT_SIZE
        size_deg: float = u.Quantity(size).to_value('deg')
        size_pix: int = int(min(
            max(float(size_deg) / im.pixel_scale, 1),
            ENV.MAXIMUM_CUTOUT_SIZE
        ))

        cmd.extend([
            '--wcs',
            f'-x {ra}',
            f'-y {dec}',
            f'-c {size_pix}',
            f'-r {size_pix}',
        ])

        # attachment file name is based on coordinates and size
        suffix = f'_{+ra:.5f}{+dec:.5f}_{size.replace(" ", "")}'

    # create attachment file name
    attachment_filename: str = os.path.splitext(
        os.path.basename(im.image_url)
    )[0]
    attachment_filename += f'{suffix}.{format}'

    # create a unique temporary file
    image_path: str
    fd, image_path = mkstemp(suffix=f'.{format}', dir=ENV.SBNSIS_CUTOUT_CACHE)
    os.close(fd)  # the file is created, let fitscut overwrite it
    cmd.extend([source_image_path, image_path])
    check_output(cmd)

    return image_path, attachment_filename
