# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Add images to database.

May be run as a command-line script via python3 -m sbn_survey_image_service.data.add

"""

import os
import logging
import argparse
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm.session import Session
from pds3 import PDS3Label
import pds4_tools

from ..exceptions import InvalidLabel, InvalidPDS3Label, InvalidPDS4Label, InvalidImagePath
from ..data import valid_pds3_label
from ..services.database_provider import data_provider_session, db_engine
from ..models import Base
from ..models.image import Image


def _remove_prefix(s: str, prefix: str):
    """If ``s`` starts with ``prefix`` remove it."""
    if s.startswith(prefix):
        return s[len(prefix):]
    else:
        return s


def add_label(label_path: str, session: Session, base_url: str = 'file://',
              strip_leading: str = '', **kwargs: Dict[str, str]) -> bool:
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

    **kwargs :
        Use these values instead of anything from the label.


    Returns
    -------
    success : bool

    """

    logger: logging.Logger = logging.getLogger(__name__)

    exc: Exception
    try:
        if valid_pds3_label(label_path):
            im = pds3_image(label_path, **kwargs)
        else:
            im = pds4_image(label_path, **kwargs)
    except (InvalidLabel, InvalidImagePath) as exc:
        logger.error(exc)
        return False

    # make proper URLs
    im.label_url = ''.join((
        base_url, _remove_prefix(im.label_url, strip_leading)
    ))
    im.image_url = ''.join((
        base_url, _remove_prefix(im.image_url, strip_leading)
    ))

    # add to database
    session.add(im)

    logger.info('Adding %s', label_path)
    return True


def pds3_image(label_path: str, **kwargs: Dict[str, str]) -> Image:
    """Examine PDS3 label for image meta data and file name.

    When adding a new PDS3-labeled survey to the service, edit this
    function so that it returns the correct image path.


    Parameters
    ----------
    label_path : str
        Path to the data label.

    **kwargs :
        Use these values instead of anything from the label.  Allowed
        keys: facility


    Returns
    -------
    im : Image

    """

    exc: Exception
    try:
        label: PDS3Label = PDS3Label(label_path)
    except Exception as exc:
        raise InvalidPDS3Label(f'Error reading {label_path}.') from exc

    im: Image = Image(
        obs_id=label['PRODUCT_ID'],
        collection=label['DATA_SET_ID'],
        facility=kwargs.get('facility', label['INSTRUMENT_HOST_NAME']),
        instrument=label['INSTRUMENT_NAME'],
        target=label['TARGET_NAME'],
        label_url=label_path
    )

    pointer: str
    if label['PRODUCT_NAME'] == "NEAT TRI-CAM IMAGE":
        pointer = '^IMAGE'
    else:
        pointer = '^IMAGE'

    im.image_url = os.path.join(
        os.path.dirname(label_path), label[pointer][0].lower())

    if not os.path.exists(im.image_url):
        # some of our archive is compressed
        im.image_url += '.fz'

    if not os.path.exists(im.image_url):
        raise InvalidImagePath(f'Could not find image in {label_path}.')

    return im


def pds4_image(label_url: str, **kwargs: Dict[str, str]) -> Image:
    """Examine PDS3 label for image data product ID and file name.

    When adding a new PDS4-labeled survey to the service, edit this
    function so that it returns the correct image path.

    """

    raise InvalidPDS4Label()


def add_directory(path: str, session: Session, recursive: bool = False,
                  extensions: Optional[List[str]] = None,
                  **kwargs: Dict[str, str]) -> None:
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
        .lbl, .xml.

    **kwargs :
        Options to pass to `add_label`.

    """

    extensions = ['.lbl', '.xml'] if extensions is None else extensions
    extensions = [x.lower() for x in extensions]

    logger: logging.Logger = logging.getLogger(__name__)
    logger.info('Searching directory %s', path)
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
                n_added += add_label(os.path.join(dirpath,
                                                  filename), session, **kwargs)

        if not recursive:
            break

    logger.info('Searched %d directories, found %d lables, %d successfully added.',
                n_dirs, n_files, n_added)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Add data to SBN Survey Image Service database.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('labels_or_directories', nargs='+',
                        help='PDS labels or directories')
    parser.add_argument('-r', action='store_true',
                        help='recursively search directories')
    parser.add_argument('-e', action='append', default=['.lbl', '.xml'],
                        help=('additional file name extensions to consider'
                              ' while searching directories'))
    parser.add_argument('--no-create', dest='create', action='store_false',
                        help='do not attempt to create missing database tables')
    parser.add_argument('--facility', help='use this facility name')
    parser.add_argument('--base-url', default='file://',
                        help='prepend this string to form a URL')
    parser.add_argument('--strip-leading', default='',
                        help='strip this leading string before forming the URL')
    return parser.parse_args()


def _main() -> None:
    args: argparse.Namespace = _parse_args()
    # options to pass on to add_* functions:
    kwargs = dict(facility=args.facility, base_url=args.base_url,
                  strip_leading=args.strip_leading.rstrip('/'))
    logging.basicConfig(level=logging.INFO)

    session: Session
    with data_provider_session() as session:
        if args.create:
            Base.metadata.create_all(db_engine)

        for ld in args.labels_or_directories:
            if os.path.isdir(ld):
                add_directory(ld, session, recursive=args.r,
                              extensions=args.e, **kwargs)
            else:
                add_label(ld, session, **kwargs)


if __name__ == '__main__':
    _main()
