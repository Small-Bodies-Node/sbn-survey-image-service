# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Data product image service."""

__all__ = ["image_query"]

import os
from copy import copy
import warnings
from enum import Enum
from typing import List, Tuple

from PIL import Image as PIL_Image
from sqlalchemy.orm.exc import NoResultFound
import numpy as np
from astropy.coordinates import Angle
import astropy.units as u
from astropy.io import fits
from astropy.time import Time
from astropy.nddata import Cutout2D
from astropy.coordinates import SkyCoord, Angle
from astropy.wcs import WCS, FITSFixedWarning
from astropy.visualization import ZScaleInterval

from .database_provider import data_provider_session, Session
from ..data import url_to_local_file, generate_cache_filename
from ..models.image import Image
from ..config.exceptions import InvalidImageID, ParameterValueError
from ..config.env import ENV
from .. import __version__ as sis_version


class ImageFormat(Enum):
    # parameter, Pillow Image format, file extension
    FITS = ("fits", "fits", "fits")
    JPEG = ("jpeg", "jpeg", "jpeg")
    JPG = ("jpg", "jpeg", "jpeg")
    PNG = ("png", "png", "png")
    DEFAULT = (None, "fits", "fits")

    def __new__(cls, parameter, format, extension):
        self = object.__new__(cls)
        self._value_ = parameter
        self.format = format
        self.extension = extension
        return self


class CutoutSpec:
    """Cutout center and size.


    Parameters
    ----------
    ra, dec : float or None
        Extract sub-frame around this position: J2000 right ascension and
        declination in degrees.

    size : str or None
        Sub-frame size in angular units, e.g., "5 arcmin".  Parsed with
        `astropy.units.Quantity`.  Minimum 1 arcsec.

    """

    MINUMUM_SIZE: Angle = Angle(1 * u.arcsec)

    def __init__(self, ra: float | None, dec: float | None, size: str | Angle | None):
        self.ra: float | None = ra
        self.dec: float | None = dec
        self.normalize()

        self.size: Angle = (
            self.MINUMUM_SIZE if size is None else max(self.MINUMUM_SIZE, Angle(size))
        )

    def __str__(self) -> str:
        if self.full_size:
            return "full_size"
        return "".join([str(x) for x in (self.ra, self.dec, self.size)])

    @property
    def full_size(self) -> bool:
        """Returns ``True`` if ``ra`` or ``dec`` is ``None``."""
        return self.coords is None

    @property
    def coords(self) -> SkyCoord | None:
        """Center as a `SkyCoord` object, or ``None``, if not defined."""
        if any((self.ra is None, self.dec is None)):
            return None
        return SkyCoord(self.ra, self.dec, unit=(u.deg, u.deg))

    def normalize(self) -> None:
        """Fix RA between 0 and 360, Dec between -90 and 90."""

        if self.ra is not None:
            # RA 0 to 360
            self.ra = self.ra % 360

        if self.dec is not None:
            # Dec -90 to 90
            self.dec = min(max(self.dec, -90), 90)

    def cutout(
        self, obs_id: str, url: str, wcs_ext: int, data_ext: int, meta: dict = {}
    ) -> str:
        """Generate a cutout from URL.


        Parameters
        ----------
        obs_id : str
            Database observation ID, i.e., PDS4 logical identifier (LID).

        url : str
            The URL to the full-size image.

        wcs_ext : int
            The FITS HDU extension with the WCS.

        data_ext : int
            The FITS HDU extension with the data to cutout.

        meta : dict, optional
            Optional metadata to add to the FITS header.


        Returns
        -------
        fn : str
            The file name of the a FITS file cutout, or, if ``self.full_size``
            is True, the full-sized FITS image.

        """

        if self.full_size:
            return url_to_local_file(url)

        fits_image_path: str = generate_cache_filename(url, str(self), "fits")

        # file exists?  done!
        if os.path.exists(fits_image_path):
            return fits_image_path

        # output data object
        result: fits.HDUList = fits.HDUList()

        # use fsspec so that we only read (and decompress) the portions of the
        # file that are needed for the cutout
        data: fits.HDUList
        options: dict = {
            "cache": False,
            "use_fsspec": True,
            "lazy_load_hdus": True,
            "fsspec_kwargs": {"block_size": 1024 * 512, "cache_type": "bytes"},
        }
        with fits.open(url, **options) as data:
            wcs_header: fits.Header = copy(data[wcs_ext].header)

            wcs: WCS
            with warnings.catch_warnings():
                warnings.simplefilter(
                    "ignore", (fits.verify.VerifyWarning, FITSFixedWarning)
                )

                # XPIXELSZ and YPIXELSZ cause wcslib to look for DSS distortion
                # keywords.  This causes failures for NEAT data.
                try:
                    wcs = WCS(wcs_header)
                except ValueError:
                    # try to fix the header
                    retry = False

                    if "XPIXELSZ" in wcs_header:
                        retry = True
                        del wcs_header["XPIXELSZ"]

                    if "YPIXELSZ" in wcs_header:
                        retry = True
                        del wcs_header["YPIXELSZ"]

                    if retry:
                        wcs = WCS(wcs_header)
                    else:
                        raise

            cutout: Cutout2D = Cutout2D(
                data[data_ext].section, self.coords, self.size, wcs=wcs
            )

            header: fits.Header = copy(data[data_ext].header)
            header.update(cutout.wcs.to_header())
            header.add_comment("Cutout generated by the SBN Survey Image Service")
            header.add_comment("NASA Planetary Data System Small-Bodies Node")
            header.add_comment(f"version {sis_version}")
            header.add_comment(f"date {Time.now().iso}")
            header["sis-oid"] = obs_id, "observation ID"
            header["sis-ra"] = self.ra, "cutout center RA (deg)"
            header["sis-dec"] = self.dec, "cutout center Dec (deg)"
            header["sis-size"] = str(self.size), "cutout size"
            for k, v in meta.items():
                header[k] = v

            result.append(fits.PrimaryHDU(cutout.data, header))
            result.writeto(fits_image_path, output_verify="silentfix")

        os.chmod(fits_image_path, 33204)

        return fits_image_path


def filename_suffix(cutout_spec: CutoutSpec, format: ImageFormat) -> str:
    """Generate the file name suffix based on query parameters.


    If any of ra/dec/size are None, then only `format` is used.

    Parameters
    ----------
    cutout_spec : CutoutSpec
        The center and size of the cutout.

    format : ImageFormat
        Returned image format: fits, png, jpeg


    Returns
    -------
    suffix : str

    """

    suffix: str = ""
    if not cutout_spec.full_size:
        # attachment file name is based on coordinates and size
        suffix = f"_{cutout_spec.ra:.5f}{cutout_spec.dec:+.5f}_{cutout_spec.size}"

    return f"{suffix}.{format.extension}"


def create_browse_image(
    fits_image_path: str,
    output_image_path: str,
    format: ImageFormat,
) -> None:
    """Create the browse (JPEG, PNG) image.


    Parameters
    ----------
    fits_image_path : str
        The source FITS image file name.

    image_path : str
        The file name of the output.

    format : ImageFormat
        The format of the output (must be JPEG, JPG, or PNG).

    """

    interval: ZScaleInterval = ZScaleInterval()
    data: np.ndarray = fits.getdata(fits_image_path)
    data = interval(data, clip=True) * 255
    image: PIL_Image = PIL_Image.fromarray(data.astype(np.uint8))
    image.save(output_image_path, format=format.format)


def image_query(
    obs_id: str,
    ra: float | None = None,
    dec: float | None = None,
    size: str | None = None,
    format: str | ImageFormat | None = None,
) -> Tuple[str, str]:
    """Query database for image file or cutout thereof.


    Temporary files are saved to the path specified by the environment variable
    SBNSIS_CUTOUT_CACHE and reused, if possible.


    Parameters
    ----------
    obs_id : str
        Database observation ID, i.e., PDS4 logical identifier (LID).

    ra, dec : float, optional
        Extract sub-frame around this position: J2000 right ascension and
        declination in degrees.

    size : str, optional
        Sub-frame size in angular units, e.g., '5arcmin'.  Parsed with
        `astropy.units.Quantity`.

    format : str or ImageFormat, optional
        Returned image format: fits, png, jpeg


    Returns
    -------
    image_path : str
        Path to requested image.

    download_filename : str
        Suggested filename for downloads.

    """

    cutout_spec: CutoutSpec = CutoutSpec(ra, dec, size)

    try:
        format = ImageFormat(format)
    except ValueError:
        raise ParameterValueError("image_query format must be fits, png, or jpeg.")

    im: Image
    session: Session
    with data_provider_session() as session:
        exc: Exception
        try:
            im = session.query(Image).filter(Image.obs_id == obs_id).one()
        except NoResultFound as exc:
            raise InvalidImageID("Image ID not found in database.") from exc

        session.expunge(im)

    # create attachment file name
    download_filename: str = os.path.splitext(os.path.basename(im.image_url))[0]
    download_filename += filename_suffix(cutout_spec, format)

    # NEAT, ATLAS: data and WCS are found in the first extension
    wcs_ext: int = 0
    data_ext: int = 0
    if ":gbo.ast.atlas.survey" or ":gbo.ast.neat.survey" in im.collection:
        wcs_ext = 1
        data_ext = 1

    # generate the cutout, as needed
    fits_image_path: str = cutout_spec.cutout(
        obs_id,
        im.image_url,
        wcs_ext,
        data_ext,
    )

    # FITS format?  done!
    if format == ImageFormat.FITS:
        return fits_image_path, download_filename

    # formulate the final image file name
    image_path = generate_cache_filename(
        im.image_url, str(cutout_spec), format.extension
    )

    # was this file already generated?  serve it!
    if os.path.exists(image_path):
        return image_path, download_filename

    # create the jpeg or png
    create_browse_image(fits_image_path, image_path, format)

    # rw-rw-r--
    # In [16]: (stat.S_IFREG | stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)
    # Out[16]: 33204
    os.chmod(image_path, 33204)

    return image_path, download_filename
