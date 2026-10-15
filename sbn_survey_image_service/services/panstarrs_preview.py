"""Normalize a PS1 preview using the header of its exact FITS cutout."""

import io
import os
import re
from tempfile import NamedTemporaryFile

import numpy as np
import requests
from astropy.io import fits
from astropy.wcs import WCS
from PIL import Image
from pyavm import AVM
from reproject import reproject_interp

from .north_up_wcs import north_up_wcs
from .preview_cache_filename import preview_cache_filename
from .skymapper_preview import MAX_HEADER_BYTES, MAX_PREVIEW_BYTES, RENDERER_VERSION

PANSTARRS_URL = "https://ps1images.stsci.edu/cgi-bin/fitscut.cgi"
IMAGE_PATTERN = (
    r"/rings\.v3\.skycell/\d{4}/\d{3}/"
    r"rings\.v3\.skycell\.\d{4}\.\d{3}\.[A-Za-z0-9_.]+\.fits"
)


def panstarrs_preview(
    image: str, ra: float, dec: float, size: int, *, cache_directory: str | None = None
) -> str:
    """Read the bounded header stream, close it, then orient the matching PNG.

    PS1's generated cutouts do not honor Range. Streaming stops at END; the
    application never reads the scientific array. getWCS describes the entire
    skycell, so it cannot locate the cutout pixels accurately enough for CAT.
    SkyMapper retains its separate strict 206-only reader.
    """
    if not re.fullmatch(IMAGE_PATTERN, image):
        raise ValueError("Invalid Pan-STARRS image identifier")
    if not (0 <= ra < 360 and -90 <= dec <= 90 and 0 < size <= 2048):
        raise ValueError("Invalid Pan-STARRS cutout position or size")
    if int(size) != size:
        raise ValueError("Pan-STARRS cutout size must be an integer")
    params = {"red": image, "ra": str(ra), "dec": str(dec), "size": str(size)}
    destination = preview_cache_filename(
        RENDERER_VERSION,
        "panstarrs",
        str(params),
        "png",
        cache_directory=cache_directory,
    )
    if os.path.exists(destination):
        return destination

    blocks = bytearray()
    with requests.get(
        PANSTARRS_URL,
        params={**params, "format": "fits"},
        stream=True,
        headers={"Accept-Encoding": "identity"},
        timeout=(10, 30),
        allow_redirects=False,
    ) as response:
        response.raise_for_status()
        if (
            response.status_code != 200
            or response.headers.get("Content-Encoding", "identity") != "identity"
        ):
            raise ValueError("Unexpected Pan-STARRS FITS response")
        for _ in range(MAX_HEADER_BYTES // 2880):
            block = response.raw.read(2880)
            if len(block) != 2880:
                raise ValueError("Incomplete Pan-STARRS FITS header")
            blocks.extend(block)
            if any(
                block[i : i + 80].startswith(b"END     ") for i in range(0, 2880, 80)
            ):
                break
        else:
            raise ValueError("Pan-STARRS header exceeds the allowed byte budget")
    header = fits.Header.fromstring(blocks.decode("ascii"), sep="")
    if not header.get("SIMPLE") or header.get("NAXIS") != 2:
        raise ValueError("Expected a primary two-dimensional Pan-STARRS FITS image")
    expected = (int(header["NAXIS1"]), int(header["NAXIS2"]))
    if min(expected) < 1 or max(expected) > 2048:
        raise ValueError("Invalid Pan-STARRS cutout dimensions")
    with requests.get(
        PANSTARRS_URL,
        params={**params, "format": "png"},
        stream=True,
        timeout=(10, 30),
        allow_redirects=False,
    ) as response:
        response.raise_for_status()
        encoded = response.raw.read(MAX_PREVIEW_BYTES + 1, decode_content=True)
    if len(encoded) > MAX_PREVIEW_BYTES:
        raise ValueError("Pan-STARRS preview exceeds the allowed byte budget")
    with Image.open(io.BytesIO(encoded)) as image_file:
        if image_file.size != expected or image_file.mode != "L":
            raise ValueError("Pan-STARRS preview and FITS geometry differ")
        pixels = np.asarray(image_file, dtype=float)[::-1]
    native = WCS(header).celestial
    if not native.has_celestial:
        raise ValueError("Pan-STARRS cutout has no celestial WCS")
    target = north_up_wcs(native, pixels.shape)
    rendered = reproject_interp(
        (pixels, native),
        target,
        shape_out=pixels.shape,
        return_footprint=False,
        order="nearest-neighbor",
    )
    with NamedTemporaryFile(
        dir=os.path.dirname(destination), suffix=".png", delete=False
    ) as tmp:
        temporary = tmp.name
    try:
        Image.fromarray(
            np.nan_to_num(rendered).clip(0, 255).astype(np.uint8)[::-1]
        ).save(temporary)
        AVM.from_wcs(target, shape=pixels.shape).embed(temporary, temporary)
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)
    return destination
