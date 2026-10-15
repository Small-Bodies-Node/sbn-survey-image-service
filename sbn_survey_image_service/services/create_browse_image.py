import os
from tempfile import NamedTemporaryFile

import numpy as np
from astropy.io import fits
from astropy.visualization import ZScaleInterval
from astropy.wcs import WCS
from PIL import Image
from pyavm import AVM
from reproject import reproject_interp

from .image_format import ImageFormat
from .north_up_wcs import north_up_wcs


def create_browse_image(
    input_image: str,
    output_image: str,
    format: ImageFormat | str,
    align: bool,
    wcs_ext: int = 0,
    data_ext: int = 0,
) -> None:
    """Render a derived JPEG/PNG and embed its actual WCS.

    FITS arrays are (height, width); CRPIX and pixel_shape are (x, y).
    The AVM describes the rendered view, including its rotation and parity.
    """
    image_format = ImageFormat(format)
    with fits.open(input_image, "readonly") as hdus:
        data = np.array(hdus[data_ext].data)
        header = hdus[wcs_ext].header.copy()
    # NEAT detector keywords otherwise make wcslib select DSS distortion.
    header.remove("XPIXELSZ", ignore_missing=True)
    header.remove("YPIXELSZ", ignore_missing=True)
    native = WCS(header).celestial
    if not native.has_celestial:
        raise ValueError("Cannot render an oriented preview without celestial WCS")
    target = north_up_wcs(native, data.shape)
    if not align:
        target.wcs.cd = native.pixel_scale_matrix
    rendered = reproject_interp(
        (data, native),
        target,
        shape_out=data.shape,
        return_footprint=False,
        order="nearest-neighbor",
    )
    scaled = (
        ZScaleInterval()(rendered, clip=True) * 255
        if np.isfinite(rendered).any()
        else np.zeros(data.shape)
    )
    pixels = (
        np.nan_to_num(scaled, nan=0, posinf=255, neginf=0)
        .clip(0, 255)
        .astype(np.uint8)[::-1]
    )
    # Publish only complete pixels plus AVM, even with simultaneous cache misses.
    with NamedTemporaryFile(
        dir=os.path.dirname(output_image) or ".",
        suffix="." + image_format.extension,
        delete=False,
    ) as temporary_file:
        temporary = temporary_file.name
    try:
        Image.fromarray(pixels).save(temporary, format=image_format.format, quality=95)
        AVM.from_wcs(target, shape=data.shape).embed(temporary, temporary)
        os.replace(temporary, output_image)
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)
