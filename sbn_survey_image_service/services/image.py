# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Data product image service."""

__all__ = ["image_query"]

import os
import subprocess
from typing import List, Optional, Tuple

from sqlalchemy.orm.exc import NoResultFound
from astropy.coordinates import Angle

from .database_provider import data_provider_session, Session
from ..data import url_to_local_file, generate_cache_filename
from ..models.image import Image
from ..config.exceptions import InvalidImageID, ParameterValueError, FitscutError
from ..config.env import ENV

FORMATS = {"png": "--png", "jpeg": "--jpg"}


def image_query(
    obs_id: str,
    ra: Optional[float] = None,
    dec: Optional[float] = None,
    size: Optional[str] = None,
    format: str = "fits",
) -> Tuple[str, str]:
    """Query database for image file or cutout thereof.


    For cutouts, fitscut may not be able to work with fpacked data.  Edit code
    branching below for files that must be funpacked first.

    Temporary files are saved to the path specified by the environment variable
    SBNSIS_CUTOUT_CACHE and reused, if possible.


    Parameters
    ----------
    obs_id : str
        PDS4 logical identifier (LID).

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

    download_filename : str
        Suggested filename for downloads.

    """

    if format not in ["fits", "png", "jpeg"]:
        raise ParameterValueError(
            "image_query format must be fits, png, or jpeg.")

    session: Session
    exc: Exception
    with data_provider_session() as session:
        try:
            im: Image = session.query(Image).filter(
                Image.obs_id == obs_id).one()
        except NoResultFound as exc:
            raise InvalidImageID("Image ID not found in database.") from exc

        session.expunge(im)

    # normalize coordinates
    if ra is not None:
        # RA 0 to 360
        ra = ra % 360

    if dec is not None:
        # Dec -90 to 90
        dec = min(max(dec, -90), 90)

    # create attachment file name
    suffix: str = ""
    if not any((ra is None, dec is None, size is None)):
        # attachment file name is based on coordinates and size
        suffix = f'_{ra:.5f}{dec:+.5f}_{size.replace(" ", "")}'

    download_filename: str = os.path.splitext(
        os.path.basename(im.image_url))[0]
    download_filename += f"{suffix}.{format}"

    # was this file already generated?  serve it!
    image_path = generate_cache_filename(
        im.image_url, obs_id, str(ra), str(dec), str(size), format
    )
    if os.path.exists(image_path):
        return image_path, download_filename

    # otherwise, get the data and process
    source_image_path: str = url_to_local_file(im.image_url)

    cmd: List[str] = ["fitscut", "-f"]

    if FORMATS.get(format) is not None:
        cmd.extend(
            [
                str(FORMATS.get(format)),
                # '--asinh-scale'
                "--autoscale=1",
            ]
        )

    if (ra is None) or (dec is None) or (size is None):
        if format == "fits":
            # full-frame fits image, we're done
            return source_image_path, os.path.basename(im.image_url)

        # full-frame jpeg or png
        cmd.append("--all")
    else:
        # cutout requested

        # cutout size is between 1 and ENV.MAXIMUM_CUTOUT_SIZE
        try:
            size_deg: float = Angle(size).deg
        except ValueError as exc:
            raise ParameterValueError(str(exc))

        size_pix: int = int(
            min(max(size_deg / im.pixel_scale, 1), ENV.MAXIMUM_CUTOUT_SIZE)
        )

        # funpack before fitscut?
        decompress: bool = False
        extension: str = ""
        if obs_id.startswith("urn:nasa:pds:gbo.ast.atlas.survey"):
            decompress = True
            extension = "image"
        # curiously, fitscut does not have an issue with fpacked NEAT data

        if decompress:
            source_image_path = _funpack(source_image_path, extension)

        cmd.extend(
            [
                "--wcs",
                f"-x {ra}",
                f"-y {dec}",
                f"-c {size_pix}",
                f"-r {size_pix}",
            ]
        )

    cmd.extend([source_image_path, image_path])

    try:
        subprocess.check_output(cmd)
    except subprocess.CalledProcessError as exc:
        raise FitscutError(
            f"""Error processing data.
Command line = {" ".join(cmd)}
Process returned: {exc.output}"""
        ) from exc

    # rw-rw-r--
    # In [16]: (stat.S_IFREG | stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)
    # Out[16]: 33204
    os.chmod(image_path, 33204)

    return image_path, download_filename


def _funpack(filename, extension):
    """Decompress an fpacked file and return the new file name."""

    decompressed_filename = generate_cache_filename(filename, extension)

    if not os.path.exists(decompressed_filename):
        cmd: List[str] = [
            "funpack",
            "-E",
            extension,
            "-O",
            decompressed_filename,
            filename,
        ]
        subprocess.check_call(cmd)

    return decompressed_filename
