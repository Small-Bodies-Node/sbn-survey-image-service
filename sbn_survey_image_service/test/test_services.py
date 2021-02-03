# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Test services using test data set."""

import os
import pytest
from sqlalchemy.orm.session import Session
import numpy as np
from astropy.io import fits
from tempfile import mkstemp

from ..data.test import generate
from ..services import data_provider_session, image_query, label_query
from ..services.image import pds3_pixel_scale
from ..env import ENV
from ..exceptions import BadPixelScale, InvalidImageID, InvalidPDS3Label


@pytest.fixture(autouse=True)
def dummy_data():
    session: Session
    with data_provider_session() as session:
        if not generate.exists(session):
            generate.create_data(session, ENV.TEST_DATA_PATH)


def test_label_query():
    image_path: str
    attachment_filename: str
    image_path, attachment_filename = label_query('test-000023-ra')
    assert image_path == os.path.join(
        ENV.TEST_DATA_PATH, 'test-000023-ra.lbl')


def test_label_query_fail():
    with pytest.raises(InvalidImageID):
        label_query('not a real ID')


def test_image_query_full_frame_fits():
    image_path: str
    attachment_filename: str
    image_path, attachment_filename = image_query(
        'test-000023-ra', format='fits')

    # should return path to original file
    assert image_path == os.path.join(
        ENV.TEST_DATA_PATH, 'test-000023-ra.fits')
    assert attachment_filename == 'test-000023-ra.fits'


def test_image_query_full_frame_jpg():
    image_path: str
    attachment_filename: str
    image_path, attachment_filename = image_query(
        'test-000023-ra', format='jpeg')

    # should return jpg file in cache directory
    assert os.path.dirname(image_path) == os.path.abspath(
        ENV.SBNSIS_CUTOUT_CACHE)
    assert os.path.splitext(image_path)[1] == '.jpeg'
    assert attachment_filename == 'test-000023-ra.jpeg'


def test_image_query_full_frame_png():
    image_path: str
    attachment_filename: str
    image_path, attachment_filename = image_query(
        'test-000023-ra', format='png')

    # should return png file in cache directory
    assert os.path.dirname(image_path) == os.path.abspath(
        ENV.SBNSIS_CUTOUT_CACHE)
    assert os.path.splitext(image_path)[1] == '.png'
    assert attachment_filename == 'test-000023-ra.png'


def test_image_query_cutout():
    ra: float = 0.0
    dec: float = -75.25
    size: str = '1deg'

    image_path: str
    attachment_filename: str
    image_path, attachment_filename = image_query(
        'test-000102-dec', ra=ra, dec=dec, size=size,
        format='fits')

    # should return fits file in cache directory
    assert os.path.dirname(image_path) == os.path.abspath(
        ENV.SBNSIS_CUTOUT_CACHE)
    assert os.path.splitext(image_path)[1] == '.fits'
    assert attachment_filename == f'test-000102-dec_{+ra:.5f}{+dec:.5f}_{size.replace(" ", "")}.fits'

    # inspect file, value should be -75 at the center
    im: np.ndarray = fits.getdata(image_path)
    assert im[im.shape[0] // 2, im.shape[1] // 2] == -75


def test_image_query_obs_id_fail():
    with pytest.raises(InvalidImageID):
        image_query('not a real obs ID')


def test_image_query_format_fail():
    with pytest.raises(ValueError):
        image_query('', format='something else')


def test_pds3_pixel_scale_invalid_label():
    fd: int
    fn: str
    fd, fn = mkstemp()
    os.close(fd)
    with open(fn, 'w') as outf:
        outf.write('''\r
This is not a PDS3 label.\r
''')
    with pytest.raises(InvalidPDS3Label):
        pds3_pixel_scale(fn)

    os.unlink(fn)


def test_pds3_pixel_scale_invalid_pixel_scale():
    fd: int
    fn: str
    fd, fn = mkstemp()
    os.close(fd)
    with open(fn, 'w') as outf:
        outf.write(f'''PDS_VERSION_ID                     = PDS3                                     \r
COMMENT                            = "Dummy label"                            \r
OBJECT                             = IMAGE                                    \r
  HORIZONTAL_PIXEL_FOV             = 11.00000 <DEGREE>                        \r
  VERTICAL_PIXEL_FOV               = 11.00000 <DEGREE>                        \r
END_OBJECT                         = IMAGE                                    \r                                                                              
END                                                                           ''')

    with pytest.raises(BadPixelScale):
        pds3_pixel_scale(fn)

    with open(fn, 'w') as outf:
        outf.write(f'''PDS_VERSION_ID                     = PDS3                                     \r
COMMENT                            = "Dummy label"                            \r
OBJECT                             = IMAGE                                    \r
  HORIZONTAL_PIXEL_FOV             = 0.000000 <DEGREE>                        \r
  VERTICAL_PIXEL_FOV               = 0.000000 <DEGREE>                        \r
END_OBJECT                         = IMAGE                                    \r                                                                              
END                                                                           ''')

    with pytest.raises(BadPixelScale):
        pds3_pixel_scale(fn)

    os.unlink(fn)
