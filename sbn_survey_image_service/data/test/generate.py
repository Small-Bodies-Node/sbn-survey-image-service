# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Create a test data set and add to database.

May be run as a command-line script via python3 -m sbn_survey_image_service.data.test.generate

"""

import os
import io
from sbn_survey_image_service.data.core import url_to_local_file
import sys
import logging
import argparse
from typing import Any, List, Tuple

import numpy as np
from sqlalchemy.orm.session import Session
from sqlalchemy.exc import OperationalError

from astropy.coordinates import SkyCoord, Angle
from astropy.io import fits
from astropy.wcs import WCS

from ..add import add_directory
from ...services.database_provider import data_provider_session, db_engine
from ...models import Base
from ...models.image import Image
from ...env import ENV


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
    """Create a test data set that partially covers the sky.

    Two sets of files are created, one with each pixel set to the RA value,
    the other with Declination.

    """

    logger: logging.Logger = logging.getLogger(__name__)

    os.system(f'mkdir -p {path}')

    # "size" of each test image: ~10 deg
    # for 1 deg...
    # N = int(4 * np.pi / ((3600 / 206265)**2))
    # N = 41253

    logger.info('Creating ~1600 images and labels.')
    centers: np.ndarray = np.degrees(spherical_distribution(400))
    image_size: int = 300
    pixel_size: float = np.degrees(
        np.sqrt(4 * np.pi / len(centers))
    ) / image_size / 10
    xy: np.ndarray = np.mgrid[:image_size, :image_size][::-1]

    w: WCS = WCS()
    w.wcs.ctype = 'RA---TAN', 'DEC--TAN'
    w.wcs.crpix = image_size // 2, image_size // 2
    w.wcs.pc = [[-pixel_size, 0], [0, pixel_size]]

    observation_number: int = 0

    c: np.ndarray
    for c in centers:
        w.wcs.crval = c
        coordinates: SkyCoord = w.pixel_to_world(xy[0], xy[1])

        data: Angle
        for data, label in zip((coordinates.ra, coordinates.dec), ('ra', 'dec')):
            observation_number += 1
            basename: str = f'test-{observation_number:06d}-{label}.fits'
            image_path: str = f'{path}/{basename}'
            label_path: str = image_path.replace('.fits', '.lbl')

            if os.path.exists(image_path) and os.path.exists(label_path):
                continue

            hdu: fits.HDUList = fits.HDUList()
            hdu.append(fits.PrimaryHDU(
                data.deg.astype(np.int32),
                header=w.to_header())
            )
            hdu.writeto(image_path, overwrite=True)

            outf: io.IOBase
            with open(label_path, 'w') as outf:
                outf.write(f'''PDS_VERSION_ID                     = PDS3                                     \r
^IMAGE                             = ("{basename}", 5)                 \r
PRODUCT_NAME                       = "SBNSIS Test Image"                      \r
PRODUCT_ID                         = "test-{observation_number:06d}-{label}"  \r
DATA_SET_ID                        = "test-collection"                        \r
INSTRUMENT_HOST_NAME               = "test-facility"                          \r
INSTRUMENT_NAME                    = "test-instrument"                        \r
TARGET_NAME                        = "test-target"                            \r
OBJECT                             = IMAGE                                    \r
  HORIZONTAL_PIXEL_FOV             = {pixel_size:.6f} <DEGREE>                        \r
  VERTICAL_PIXEL_FOV               = {pixel_size:.6f} <DEGREE>                        \r
END_OBJECT                         = IMAGE                                    \r
END                                                                           ''')

            if observation_number % 1000 == 0:
                logger.info(observation_number)

    add_directory(ENV.TEST_DATA_PATH, session)

    logger.info(
        'Created and added %d test images and their labels to the database.',
        observation_number
    )


def create_tables() -> None:
    """Create data tables, as needed."""
    Base.metadata.create_all(db_engine)


def delete_data(session) -> None:
    """Delete test data from database."""

    (
        session.query(Image)
        .filter(Image.collection == 'test-collection')
        .delete()
    )


def exists(session) -> bool:
    """Test for the existence of the test data set.

    A simple database query and file check.

    """

    try:
        results: Any = (
            session.query(Image)
            .filter(Image.collection == 'test-collection')
            .all()
        )
    except OperationalError:
        return False

    if len(results) == 0:
        return False

    im: Image
    for im in results:
        if not any((os.path.exists(url_to_local_file(im.image_url)),
                    os.path.exists(url_to_local_file(im.label_url)))):
            return False

    return True


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Add/delete test data to/from SBN Survey Image Service database.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--path', default=ENV.TEST_DATA_PATH,
                        help='directory to which to save test data files')
    parser.add_argument('--add', action='store_true',
                        help='add/create test data set')
    parser.add_argument('--exists', action='store_true',
                        help='test for the existence of the test data set')
    parser.add_argument('--delete', action='store_true',
                        help='delete test data files and database rows')
    parser.add_argument('--no-create-tables', action='store_true',
                        help='do not attempt to create missing database tables')
    args: argparse.Namespace = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return args


def _main() -> None:
    args: argparse.Namespace = _parse_args()
    logging.basicConfig(level=logging.INFO)
    logger: logging.Logger = logging.getLogger(__name__)

    session: Session
    with data_provider_session() as session:
        if args.no_create_tables is False:
            create_tables()

        if args.add:
            create_data(session, args.path)
        elif args.delete:
            delete_data(session)
            logger.info(
                'Database cleaned, but test files must be removed manually.')
        elif args.exists:
            if exists(session):
                print('Test data set appears to be valid.')
            else:
                print('Test data set is broken or missing.')


if __name__ == '__main__':
    _main()
