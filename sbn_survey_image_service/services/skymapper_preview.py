"""SkyMapper DR4 preview normalization without downloading scientific pixels."""

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

SKYMAPPER_URL = "https://api.skymapper.nci.org.au/public/siap/dr4/get_image"
RENDERER_VERSION = "north-up-v1"
MAX_HEADER_BYTES = 2880 * 32
MAX_PREVIEW_BYTES = 8 * 1024 * 1024


def read_fits_header(url: str, params: dict[str, str], session=requests) -> fits.Header:
    """Read bounded FITS blocks. Refuse 200 responses; never fall back to a full FITS."""
    blocks = bytearray()
    for offset in range(0, MAX_HEADER_BYTES, 2880):
        with session.get(
            url,
            params=params,
            headers={
                "Range": f"bytes={offset}-{offset + 2879}",
                "Accept-Encoding": "identity",
            },
            stream=True,
            timeout=(10, 30),
            allow_redirects=False,
        ) as response:
            content_range = response.headers.get("Content-Range", "")
            if response.status_code != 206 or not re.fullmatch(
                rf"bytes {offset}-{offset + 2879}/\d+", content_range
            ):
                raise ValueError(
                    "SkyMapper did not honor the requested FITS byte range"
                )
            if response.headers.get("Content-Encoding", "identity") != "identity":
                raise ValueError("Compressed FITS byte ranges cannot be used")
            block = response.raw.read(2881)
            if len(block) != 2880:
                raise ValueError("Incomplete FITS header block")
            blocks.extend(block)
        if any(block[i : i + 80].startswith(b"END     ") for i in range(0, 2880, 80)):
            header = fits.Header.fromstring(blocks.decode("ascii"), sep="")
            if not header.get("SIMPLE") or header.get("NAXIS") != 2:
                raise ValueError("Expected a primary two-dimensional FITS image")
            return header
    raise ValueError("FITS header exceeds the allowed byte budget")


def skymapper_preview(
    image: str,
    ra: float,
    dec: float,
    size: float,
    *,
    cache_directory: str | None = None,
) -> str:
    """Return a cached north-up PNG with AVM for that exact IMAGE/POS/SIZE cutout.

    SkyMapper PNGs flip native FITS Y; PA=180 PNGs additionally rotate 180°.
    Reconstruct native pixel order before applying the complete TPV WCS.
    Unsupported position angles and mismatched dimensions fail explicitly.
    """
    if not re.fullmatch(r"\d{14}-\d{2}", image):
        raise ValueError("Invalid SkyMapper IMAGE identifier")
    if not (0 <= ra < 360 and -90 <= dec <= 90 and 0 < size < 1 / 6):
        raise ValueError("Invalid cutout position or size (maximum is 10 arcmin)")
    params = {"IMAGE": image, "POS": f"{ra},{dec}", "SIZE": str(size)}
    destination = preview_cache_filename(
        RENDERER_VERSION,
        "skymapper",
        str(params),
        "png",
        cache_directory=cache_directory,
    )
    if os.path.exists(destination):
        return destination

    header = read_fits_header(SKYMAPPER_URL, {**params, "FORMAT": "fits"})
    angle = float(header["ROTSKYPA"]) % 360
    pa180 = abs(angle - 180) < 1
    if not (min(angle, 360 - angle) < 1 or pa180):
        raise ValueError("SkyMapper PNG transform is unknown for this position angle")
    with requests.get(
        SKYMAPPER_URL,
        params={**params, "FORMAT": "png"},
        stream=True,
        timeout=(10, 30),
        allow_redirects=False,
    ) as response:
        response.raise_for_status()
        encoded = response.raw.read(MAX_PREVIEW_BYTES + 1, decode_content=True)
    if len(encoded) > MAX_PREVIEW_BYTES:
        raise ValueError("SkyMapper preview exceeds the allowed byte budget")
    expected = (int(header["NAXIS1"]), int(header["NAXIS2"]))
    if max(expected) > 2048 or min(expected) < 1:
        raise ValueError("Invalid SkyMapper cutout dimensions")
    with Image.open(io.BytesIO(encoded)) as image_file:
        if image_file.size != expected:
            raise ValueError("SkyMapper PNG and FITS dimensions differ")
        if image_file.mode != "L":
            raise ValueError("Expected a grayscale SkyMapper preview")
        pixels = np.asarray(image_file, dtype=float)
    if pa180:
        pixels = pixels[::-1, ::-1]
    pixels = pixels[::-1]  # top-left PNG to bottom-left FITS coordinates
    native = WCS(header).celestial
    target = north_up_wcs(native, pixels.shape)
    rendered = reproject_interp(
        (pixels, native),
        target,
        shape_out=pixels.shape,
        return_footprint=False,
        order="nearest-neighbor",
    )
    # Atomic publication prevents a simultaneous request from seeing a partial PNG.
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
