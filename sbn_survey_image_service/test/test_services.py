# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Test services using test data set."""

import os
import pytest
import tempfile

from sqlalchemy.orm.session import Session
from PIL import Image

import numpy as np
from astropy.wcs import WCS
from astropy.io import fits
from astropy.coordinates import Angle

from ..data.test import generate
from ..data import generate_cache_filename
from ..services.database_provider import data_provider_session
from ..services.image import image_query, create_browse_image
from ..services.label import label_query
from ..config.env import ENV
from ..config.exceptions import InvalidImageID, ParameterValueError


@pytest.fixture(autouse=True)
def dummy_data():
    session: Session
    with data_provider_session() as session:
        if not generate.exists(session):
            generate.create_tables()
            generate.create_data(session, ENV.TEST_DATA_PATH)


def test_label_query():
    image_path: str
    download_filename: str
    image_path, download_filename = label_query(
        "urn:nasa:pds:survey:test-collection:test-000039"
    )
    assert image_path == os.path.join("file://", ENV.TEST_DATA_PATH, "test-000039.xml")


def test_label_query_fail():
    with pytest.raises(InvalidImageID):
        label_query("not a real ID")


def test_image_query_full_frame_fits():
    image_path: str
    download_filename: str
    image_path, download_filename = image_query(
        "urn:nasa:pds:survey:test-collection:test-000023", format="fits"
    )

    # should return path to original file
    assert image_path == os.path.join(ENV.TEST_DATA_PATH, "test-000023.fits")
    assert download_filename == "test-000023.fits"


def test_image_query_full_frame_jpg():
    image_path: str
    download_filename: str
    image_path, download_filename = image_query(
        "urn:nasa:pds:survey:test-collection:test-000023", format="jpeg"
    )

    expected_path: str = generate_cache_filename(
        "file://" + os.path.join(ENV.TEST_DATA_PATH, "test-000023.fits"),
        "full_size",
        "jpeg",
        "False",
    )

    # should return a file in the cache directory
    assert os.path.dirname(image_path) == os.path.abspath(ENV.SBNSIS_CUTOUT_CACHE)
    assert image_path == expected_path
    assert download_filename == "test-000023.jpeg"


def test_image_query_full_frame_png():
    image_path: str
    download_filename: str
    image_path, download_filename = image_query(
        "urn:nasa:pds:survey:test-collection:test-000023", format="png"
    )

    expected_path: str = generate_cache_filename(
        "file://" + os.path.join(ENV.TEST_DATA_PATH, "test-000023.fits"),
        "full_size",
        "png",
        "False",
    )

    # should return a file in the cache directory
    assert os.path.dirname(image_path) == os.path.abspath(ENV.SBNSIS_CUTOUT_CACHE)
    assert image_path == expected_path
    assert download_filename == "test-000023.png"


def test_image_query_cutout():
    ra: float = 0
    dec: float = -25
    size: str = Angle("1deg")

    image_path: str
    download_filename: str
    image_path, download_filename = image_query(
        "urn:nasa:pds:survey:test-collection:test-000102",
        ra=ra,
        dec=dec,
        size=size,
        format="fits",
    )

    expected_path: str = generate_cache_filename(
        "file://" + os.path.join(ENV.TEST_DATA_PATH, "test-000102.fits"),
        str(ra),
        str(dec),
        str(size),
        "fits",
    )

    # should return fits file in cache directory
    assert os.path.dirname(image_path) == os.path.abspath(ENV.SBNSIS_CUTOUT_CACHE)
    assert image_path == expected_path
    assert download_filename == f"test-000102_{+ra:.5f}{+dec:.5f}_{size}.fits"

    # inspect file, value should be -25 at the center
    im: np.ndarray = fits.getdata(image_path)
    assert im[im.shape[0] // 2, im.shape[1] // 2] == -25


def test_image_query_obs_id_fail():
    with pytest.raises(InvalidImageID):
        image_query("not a real obs ID")


def test_image_query_format_fail():
    with pytest.raises(ParameterValueError):
        image_query("", format="something else")


def test_create_browse_image_alignment():
    im = np.zeros((10, 10))
    im[0, :] = 1  # first row is 1111111

    wcs = WCS()
    wcs.pixel_shape = im.shape
    wcs.wcs.ctype = "RA---TAN", "DEC--TAN"
    wcs.wcs.crpix = (3, 4)
    wcs.wcs.crval = (10, 20)
    wcs.wcs.pc = [[0.5, 0], [0, -0.5]]

    with tempfile.NamedTemporaryFile("w+b", delete=False) as dataf:
        # write our test data to a FITS file
        fits.writeto(dataf, im, wcs.to_header())
        dataf.close()

        # convert the FITS to JPEG and verify the orientation
        with tempfile.NamedTemporaryFile("w+b", delete=False) as imf:
            imf.close()
            create_browse_image(dataf.name, imf.name, "jpeg", False, 0, 0)
            data = np.array(Image.open(imf.name, formats=["jpeg"]))
            # JPEGs are drawn top to bottom, so the 1111111 row is first in the
            # array
            assert all(data[0, :] == 0)
            assert all(data[-1, :] == 255)

        # convert FITS to JPEG with north up
        with tempfile.NamedTemporaryFile("w+b", delete=False) as alignedf:
            alignedf.close()
            create_browse_image(dataf.name, alignedf.name, "jpeg", True, 0, 0)
            data = np.array(Image.open(alignedf.name, formats=["jpeg"]))
            # now the 1111111 row is last
            assert all(data[0, :] == 255)
            assert all(data[-1, :] == 0)

    for f in (dataf, imf, alignedf):
        os.unlink(f.name)
