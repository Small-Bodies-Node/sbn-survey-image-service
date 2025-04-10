# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Test services using test data set."""

import os
import tempfile

import numpy as np
from astropy.wcs import WCS
from astropy.io import fits
from pyavm import AVM

from ..services.image import create_browse_image


def test_avm_xmp():
    im = np.zeros((10, 10))
    im[0, :] = 1  # first row is 1111111

    wcs = WCS()
    wcs.pixel_shape = im.shape
    wcs.wcs.ctype = "RA---TAN", "DEC--TAN"
    wcs.wcs.crpix = (3, 4)
    wcs.wcs.crval = (10, 20)
    wcs.wcs.pc = [[1, 0], [0, 1]]
    wcs.wcs.cdelt = -0.5, 0.5

    with tempfile.NamedTemporaryFile("w+b", delete=False) as dataf:
        # write our test data to a FITS file
        fits.writeto(dataf, im, wcs.to_header())
        dataf.close()

        # convert the FITS to JPEG and verify the XMP metadata
        with tempfile.NamedTemporaryFile("w+b", delete=False) as imf:
            imf.close()
            create_browse_image(dataf.name, imf.name, "jpeg", False, 0, 0)

            avm = AVM.from_image(imf.name)

    expected_reference_value = wcs.pixel_to_world_values(4.5, 4.5)  # 0-based
    assert avm.Spatial.CoordinateFrame == "ICRS"
    assert avm.Spatial.ReferenceValue[0] == expected_reference_value[0]
    assert avm.Spatial.ReferenceValue[1] == expected_reference_value[1]
    assert avm.Spatial.ReferencePixel[0] == 5.5  # 1-based
    assert avm.Spatial.ReferencePixel[1] == 5.5
    assert avm.Spatial.Scale[0] == -0.5
    assert avm.Spatial.Scale[1] == 0.5
    assert avm.Spatial.Rotation == 0
    assert avm.Spatial.CoordsystemProjection == "TAN"
    assert avm.Spatial.Quality == "Full"

    for f in (dataf, imf):
        os.unlink(f.name)


def test_atlas_avm():
    """ATLAS has a more complex WCS."""

    im = np.zeros((10, 10))
    im[0, :] = 1  # first row is 1111111

    wcs = WCS()
    wcs.pixel_shape = im.shape
    wcs.wcs.ctype = "RA---TAN", "DEC--TAN"
    wcs.wcs.crpix = -877.0, 2175.0
    wcs.wcs.crval = 83.10288, 20.93041
    wcs.wcs.pc = [
        [0.0005174308599615, 1.535411458754e-06],
        [1.457055759615e-06, -0.000517310147702],
    ]
    wcs.wcs.cdelt = 1, 1

    with tempfile.NamedTemporaryFile("w+b", delete=False) as dataf:
        # write our test data to a FITS file
        fits.writeto(dataf, im, wcs.to_header())
        dataf.close()

        # convert the FITS to JPEG and verify the XMP metadata
        with tempfile.NamedTemporaryFile("w+b", delete=False) as imf:
            imf.close()
            create_browse_image(dataf.name, imf.name, "jpeg", False, 0, 0)

            avm = AVM.from_image(imf.name)

    expected_reference_value = wcs.pixel_to_world_values(4.5, 4.5)  # 0-based
    assert avm.Spatial.CoordinateFrame == "ICRS"
    assert avm.Spatial.ReferenceValue[0] == expected_reference_value[0]
    assert avm.Spatial.ReferenceValue[1] == expected_reference_value[1]
    assert avm.Spatial.ReferencePixel[0] == 5.5  # 1-based
    assert avm.Spatial.ReferencePixel[1] == 5.5
    assert np.isclose(avm.Spatial.CDMatrix[0], 0.0005174308599615)
    assert np.isclose(avm.Spatial.CDMatrix[1], 1.535411458754e-06)
    assert np.isclose(avm.Spatial.CDMatrix[2], 1.457055759615e-06)
    assert np.isclose(avm.Spatial.CDMatrix[3], -0.000517310147702)
    assert avm.Spatial.CoordsystemProjection == "TAN"
    assert avm.Spatial.Quality == "Full"

    for f in (dataf, imf):
        os.unlink(f.name)
