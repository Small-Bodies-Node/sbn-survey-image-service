# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Test services using test data set."""

import os
import pytest
from sqlalchemy.orm.session import Session
import numpy as np
from astropy.io import fits

from ..data.test import generate
from ..services import data_provider_session, image_query, label_query
from ..env import ENV
from ..exceptions import InvalidImageID, ParameterValueError


@pytest.fixture(autouse=True)
def dummy_data():
    session: Session
    with data_provider_session() as session:
        if not generate.exists(session):
            generate.create_tables()
            generate.create_data(session, ENV.TEST_DATA_PATH)


def test_label_query():
    image_url: str
    attachment_filename: str
    image_url, attachment_filename = label_query('test-000023-ra')
    assert image_url == os.path.join(
        'file://', ENV.TEST_DATA_PATH, 'test-000023-ra.lbl')


def test_label_query_fail():
    with pytest.raises(InvalidImageID):
        label_query('not a real ID')


def test_image_query_full_frame_fits():
    image_url: str
    attachment_filename: str
    image_url, attachment_filename = image_query(
        'test-000023-ra', format='fits')

    # should return path to original file
    assert image_url == os.path.join(
        ENV.TEST_DATA_PATH, 'test-000023-ra.fits')
    assert attachment_filename == 'test-000023-ra.fits'


def test_image_query_full_frame_jpg():
    image_url: str
    attachment_filename: str
    image_url, attachment_filename = image_query(
        'test-000023-ra', format='jpeg')

    # should return jpg file in cache directory
    assert os.path.dirname(image_url) == os.path.abspath(
        ENV.SBNSIS_CUTOUT_CACHE)
    assert os.path.splitext(image_url)[1] == '.jpeg'
    assert attachment_filename == 'test-000023-ra.jpeg'


def test_image_query_full_frame_png():
    image_url: str
    attachment_filename: str
    image_url, attachment_filename = image_query(
        'test-000023-ra', format='png')

    # should return png file in cache directory
    assert os.path.dirname(image_url) == os.path.abspath(
        ENV.SBNSIS_CUTOUT_CACHE)
    assert os.path.splitext(image_url)[1] == '.png'
    assert attachment_filename == 'test-000023-ra.png'


def test_image_query_cutout():
    ra: float = 43.2
    dec: float = -45.0
    size: str = '1deg'

    image_url: str
    attachment_filename: str
    image_url, attachment_filename = image_query(
        'test-000102-dec', ra=ra, dec=dec, size=size,
        format='fits')

    # should return fits file in cache directory
    assert os.path.dirname(image_url) == os.path.abspath(
        ENV.SBNSIS_CUTOUT_CACHE)
    assert os.path.splitext(image_url)[1] == '.fits'
    assert attachment_filename == f'test-000102-dec_{+ra:.5f}{+dec:.5f}_{size.replace(" ", "")}.fits'

    # inspect file, value should be -45 at the center
    im: np.ndarray = fits.getdata(image_url)
    assert im[im.shape[0] // 2, im.shape[1] // 2] == -45


def test_image_query_obs_id_fail():
    with pytest.raises(InvalidImageID):
        image_query('not a real obs ID')


def test_image_query_format_fail():
    with pytest.raises(ParameterValueError):
        image_query('', format='something else')
