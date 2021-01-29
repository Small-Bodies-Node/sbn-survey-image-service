# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Create a test data set and add to database.

May be run as a command-line script via python3 -m sbn_survey_image_service.data.test

"""

import os
import io
import logging
import argparse
from typing import List, Tuple

import numpy as np
from sqlalchemy.orm.session import Session

from astropy.coordinates import SkyCoord, Angle
from astropy.io import fits
from astropy.wcs import WCS

from ..services.database_provider import data_provider_session, db_engine
from ..models import Base
from ..models.image import Image


def spherical_distribution(N: int) -> np.ndarray:
    """Equally distributed points on a unit sphere.

    Parameters
    ----------
    N : int
      The approximate number of points.

    Returns
    -------
    p : ndarray
      Spherical coordinates of the points, `(lambda, beta)`, in radians
      with the shape `Nx2`.

    Notes
    -----
    Based on https://www.cmu.edu/biolphys/deserno/pdf/sphere_equi.pdf
    by Markus Deserno.

    Modified from mskpy, copyright (c) 2020, Michael S. P. Kelley

    """

    pi: float = np.pi
    a: float = 4 * pi / N
    d: float = np.sqrt(a)
    Mth: int = int(np.round(pi / d))
    dth: float = pi / Mth
    dph: float = a / dth
    p: List[Tuple[float, float]] = []
    m: int
    for m in range(Mth):
        th: float = pi * (m + 0.5) / Mth
        Mph: int = int(np.round(2 * pi * np.sin(th) / dph))
        n: int
        for n in range(Mph):
            phi: float = 2 * pi * n / Mph
            p.append((phi, th - pi / 2))

    return np.array(p)


def create_data(session, path):
    """Create a test data set that covers the sky.

    Two sets of files are created, one with each pixel set to the RA value,
    the other with Declination.

    """

    logger: logging.Logger = logging.getLogger(__name__)

    os.system(f'mkdir -p {path}')

    # "size" of each test image: ~10 deg
    # for 1 deg...
    # N = int(4 * np.pi / ((3600 / 206265)**2))
    # N = 41253

    logger.info('Creating ~8000 images and labels.')
    centers: np.ndarray = np.degrees(spherical_distribution(4000))
    image_size: int = 300
    pixel_size: float = np.degrees(
        np.sqrt(4 * np.pi / len(centers))
    ) / image_size
    xy: np.ndarray = np.mgrid[:image_size, :image_size][::-1]

    w: WCS = WCS()
    w.wcs.ctype = 'RA---TAN', 'DEC--TAN'
    w.wcs.crpix = image_size // 2, image_size // 2
    w.wcs.pc = [[pixel_size, 0], [0, -pixel_size]]

    observation_number: int = 0

    c: np.ndarray
    for c in centers:
        w.wcs.crval = c
        coordinates: SkyCoord = w.pixel_to_world(xy[0], xy[1])

        data: Angle
        for data, label in zip((coordinates.ra, coordinates.dec), ('ra', 'dec')):
            observation_number += 1
            image_path: str = f'{path}/{label}_{c[0]:.5f}_{c[1]:.5f}.fits'
            label_path: str = image_path.replace('.fits', '.lbl')

            hdu: fits.HDUList = fits.HDUList()
            hdu.append(fits.PrimaryHDU(
                data.deg.astype(np.int32),
                header=w.to_header())
            )
            hdu.writeto(image_path, overwrite=True)

            outf: io.IOBase
            with open(label_path, 'w') as outf:
                outf.write(f'''
Test dummy label
----------------
RA, Dec = {c}
Coordinate values = {label}
''')

            im: Image = Image(
                obs_id=f'test-{observation_number}',
                collection='test-collection',
                facility='test-facility',
                instrument='test-instrument',
                target='test-sky',
                label_path=label_path,
                image_path=image_path
            )
            session.add(im)

            if observation_number % 1000 == 0:
                logger.info(observation_number)

    logger.info(
        'Created and added %d test images and their labels to the database.',
        observation_number
    )


def delete_data(session) -> None:
    """Delete test data from database."""

    (
        session.query(Image)
        .filter(Image.collection == 'test-collection')
        .delete()
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Add/delete test data to/from SBN Survey Image Service database.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--path', default=os.path.abspath('./data/test'),
                        help='directory to which to save test data files')
    parser.add_argument('--delete', action='store_true',
                        help='delete test data files and database rows')
    parser.add_argument('--no-create', dest='create', action='store_false',
                        help='do not attempt to create missing database tables')
    return parser.parse_args()


def _main() -> None:
    args: argparse.Namespace = _parse_args()
    logging.basicConfig(level=logging.INFO)
    logger: logging.Logger = logging.getLogger(__name__)

    session: Session
    with data_provider_session() as session:
        if args.create:
            Base.metadata.create_all(db_engine)

        if args.delete:
            delete_data(session)
            logger.info(
                'Database cleaned, but test files must be removed manually.')
        else:
            create_data(session, args.path)


if __name__ == '__main__':
    _main()
