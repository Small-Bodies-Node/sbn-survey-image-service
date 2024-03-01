# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Add images to database.

May be run as a command-line script via python3 -m sbn_survey_image_service.data.add

"""

import os
import logging
import argparse
from urllib.parse import urlparse, urlunparse
from typing import Dict, List, Optional, Union
import xml.etree.ElementTree as ET

import numpy as np
from sqlalchemy.orm.session import Session
from pds4_tools.reader.read_label import read_label as pds4_read_label

from ..exceptions import (
    LabelError,
    InvalidNEATImage,
    InvalidATLASImage,
    PDS4LabelError,
    InvalidImageURL,
    SBNSISWarning,
)
from ..services.database_provider import data_provider_session, db_engine
from ..models import Base
from ..models.image import Image
from ..logging import get_logger


def _remove_prefix(s: str, prefix: str):
    """If ``s`` starts with ``prefix`` remove it."""
    if s.startswith(prefix):
        return s[len(prefix) :]
    else:
        return s


def _normalize_url(url):
    """light normalization?"""
    return urlunparse(urlparse(url))


# Translate PDS4 processing level to IVOA ObsCore calib_level
PDS4CalibrationLevel = {"Calibrated": 2, "Partially Processed": 1}


def add_label(
    label_path: str,
    session: Session,
    base_url: str = "file://",
    strip_leading: str = "",
) -> bool:
    """Add label and image data to database.


    Parameters
    ----------
    label_path : string
        Local path to PDS label.

    session : sqlalchemy Session
        Database session object.

    base_url : str, optional
        Prepend the file path with this string to form a URL.  Default is to
        use file://.

    strip_leading : str, optional
        Remove this leading string from the path before forming the URL.


    Returns
    -------
    success : bool
        False, if the target already exists in the database.

    """

    logger: logging.Logger = get_logger()

    exc: Exception
    try:
        im = pds4_image(label_path)
    except SBNSISWarning as exc:
        logger.warning(exc)
        return False
    except (LabelError, InvalidImageURL) as exc:
        logger.error(exc)
        return False

    # make proper URLs
    im.label_url = _normalize_url(
        "".join((base_url, _remove_prefix(im.label_url, strip_leading)))
    )
    im.image_url = _normalize_url(
        "".join((base_url, _remove_prefix(im.image_url, strip_leading)))
    )

    count = session.query(Image).where(Image.obs_id == im.obs_id).count()
    if count != 0:
        # obs_id already exists
        return False

    # add to database
    session.add(im)

    logger.debug("Adding %s", label_path)
    return True


def pds4_image(label_path: str) -> Image:
    """Examine PDS4 label for image data product ID and file name.

    This function may need to be edited when adding a new
    PDS4-labeled survey to the service.


    Parameters
    ----------
    label_path : str
        Path to the data label.

    Returns
    -------
    im : Image

    """

    exc: Exception
    try:
        # data: StructureList = pds4_read(label_path, lazy_load=True)
        label: ET.ElementTree = pds4_read_label(
            label_path, enforce_default_prefixes=True
        )
    except Exception as exc:
        raise PDS4LabelError(str(exc)) from exc

    try:
        lid: str = label.find("Identification_Area/logical_identifier").text
        im: Image = Image(
            obs_id=lid,
            collection=":".join(lid.split(":")[:5]),
            # split and join in case of line feed characters
            facility=" ".join(
                label.find(
                    "Observation_Area/Observing_System/Observing_System_Component"
                    "/Internal_Reference/[reference_type='is_telescope']/../name"
                ).text.split()
            ),
            instrument=" ".join(
                label.find(
                    "Observation_Area/Observing_System/Observing_System_Component"
                    "/Internal_Reference/[reference_type='is_instrument']/../name"
                ).text.split()
            ),
            target=label.find("Observation_Area/Target_Identification/name").text,
            calibration_level=PDS4CalibrationLevel[
                label.find(
                    "Observation_Area/Primary_Result_Summary/processing_level"
                ).text
            ],
            pixel_scale=pds4_pixel_scale(label),
            label_url=label_path,
            # return the first file name found
            image_url=os.path.join(
                os.path.dirname(label_path),
                label.find("File_Area_Observational/File/file_name").text,
            ),
        )
    except AttributeError as exc:
        # probably not a useful label
        raise PDS4LabelError(str(exc)) from exc

    # is this in a recognized data collection that needs special handling?
    fz_compressed: bool = False  # some of our archive is compressed
    if lid.startswith("urn:nasa:pds:gbo.ast.neat.survey"):
        fz_compressed = True
        if not valid_neat_image(label):
            raise InvalidNEATImage(
                f"{label_path} does not appear to be a NEAT on-sky image."
            )
        if "geodss" in lid:
            im.pixel_scale = 1.43 / 3600
        elif "tricam" in lid:
            im.pixel_scale = 1.01 / 3600
    elif lid.startswith("urn:nasa:pds:gbo.ast.atlas.survey"):
        # local ATLAS archive is compressed
        fz_compressed = True
        if not valid_atlas_image(label):
            raise InvalidATLASImage(
                f"{label_path} does not appear to be an " "ATLAS prime image."
            )

    if fz_compressed:
        im.image_url += ".fz"

    return im


def pds4_pixel_scale(label: ET.ElementTree) -> Union[float, None]:
    """Compute average pixel scale from Earth_Based_Telescope discipline dictionary."""

    wcs: ET.ElementTree = label.find(
        ".//ebt:World_Coordinate_System",
        namespaces={"ebt": "http://pds.nasa.gov/pds4/ebt/v1"},
    )

    if wcs is None:
        return None

    matches: List[ET.ElementTree] = wcs.findall(
        "ebt:Coordinate_Frame_Transformation_Matrix/ebt:Transformation_Element/ebt:element_value",
        namespaces={"ebt": "http://pds.nasa.gov/pds4/ebt/v1"},
    )
    elements: List[float] = [float(x.text) for x in matches]

    if len(elements) != 4:
        return None

    cdelt: float = np.sqrt(
        np.abs(elements[0] * elements[3]) + np.abs(elements[1] * elements[2])
    )
    return cdelt


def valid_neat_image(label: ET.ElementTree) -> bool:
    """Only ingest NEAT survey on-sky images."""

    try:
        title: str = label.find("Identification_Area/title").text
    except AttributeError:
        return False
    return title in ["NEAT TRI-CAM IMAGE", "NEAT GEODSS IMAGE"]


def valid_atlas_image(label: ET.ElementTree) -> bool:
    """Only ingest ATLAS reduced images.

    If the LID ends in _fits then it is probably what we want.

    """

    lid: str = label.find("Identification_Area/logical_identifier").text
    return lid.endswith("_fits")


def add_directory(
    path: str,
    session: Session,
    recursive: bool = False,
    extensions: Optional[List[str]] = None,
    **kwargs,
) -> None:
    """Search directory for labels and add to database.


    Parameters
    ----------
    path : string
        Directory to search.

    session : sqlalchemy Session
        Database session object.

    recursive : bool, optional
        Set to ``True`` to recursively search directory.

    extensions : list of strings, optional
        Files with these extensions are consdiered PDS labels.  Default:
        .xml.

    **kwargs
        Keyword arguments for ``add_label``.

    """

    extensions = [".xml"] if extensions is None else extensions
    extensions = [x.lower() for x in extensions]

    logger: logging.Logger = get_logger()
    logger.info("Searching directory %s", path)
    n_files: int = 0
    n_added: int = 0
    n_dirs: int = 0
    for contents in os.walk(path):
        n_dirs += 1
        dirpath: str = contents[0]
        filenames: List[str] = contents[2]
        filename: str
        for filename in filenames:
            if os.path.splitext(filename)[1].lower() in extensions:
                n_files += 1
                n_added += add_label(os.path.join(dirpath, filename), session, **kwargs)

        if not recursive:
            break

    logger.info(
        "Searched %d directories, found %d labels, %d processed.",
        n_dirs,
        n_files,
        n_added,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add data to SBN Survey Image Service database.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "labels_or_directories", nargs="+", help="PDS labels or directories"
    )
    parser.add_argument(
        "-r", action="store_true", help="recursively search directories"
    )
    parser.add_argument(
        "-e",
        action="append",
        default=[".xml"],
        help=(
            "additional file name extensions to consider" " while searching directories"
        ),
    )
    parser.add_argument(
        "--no-create",
        dest="create",
        action="store_false",
        help="do not attempt to create missing database tables",
    )
    parser.add_argument(
        "--base-url", default="file://", help="prepend this string to form a URL"
    )
    parser.add_argument(
        "--strip-leading",
        default="",
        help="strip this leading string before forming the URL",
    )
    parser.add_argument("-v", action="store_true", help="verbose logging")
    return parser.parse_args()


def _main() -> None:
    args: argparse.Namespace = _parse_args()

    logger: logging.Logger = get_logger()
    logger.setLevel(logging.DEBUG if args.v else logging.INFO)

    # options to pass on to add_* functions:
    kwargs = dict(base_url=args.base_url, strip_leading=args.strip_leading.rstrip("/"))
    session: Session
    with data_provider_session() as session:
        if args.create:
            Base.metadata.create_all(db_engine)

        for ld in args.labels_or_directories:
            if os.path.isdir(ld):
                add_directory(
                    ld, session, recursive=args.r, extensions=args.e, **kwargs
                )
            else:
                add_label(ld, session, **kwargs)


if __name__ == "__main__":
    _main()
