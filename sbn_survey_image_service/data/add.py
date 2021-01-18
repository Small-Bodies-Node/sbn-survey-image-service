# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Add images to database.

May be run as a command-line script via python3 -m sbn_survey_image_service.data.add

"""

import os
import logging
import argparse
from typing import List, Optional, Tuple

from sqlalchemy.orm.session import Session
from pds3 import PDS3Label
import pds4_tools


from ..exceptions import InvalidLabel, InvalidPDS3Label, InvalidPDS4Label, InvalidImagePath
from ..data import valid_pds3_label
from ..services.database_provider import data_provider_session, db_engine
from ..models import Image, Base


def add_label(label_path: str, session: Session) -> bool:
    """Add label and image data to database.


    Parameters
    ----------
    label_path : string
        PDS label file name.

    session : sqlalchemy Session
        Database session object.


    Returns
    -------
    success : bool

    """

    logger: logging.Logger = logging.getLogger(__name__)

    exc: Exception
    try:
        image_id: str
        image_path: str
        if valid_pds3_label(label_path):
            image_id, image_path = pds3_image(label_path)
        else:
            image_id, image_path = pds4_image(label_path)
    except (InvalidLabel, InvalidImagePath) as exc:
        logger.error(exc)
        return False

    # add to database
    session.add(
        Image(
            image_id=image_id,
            image_path=image_path,
            label_path=label_path
        )
    )

    logger.error('Adding %s', label_path)
    return True


def pds3_image(label_path: str) -> Tuple[str, str]:
    """Examine PDS3 label for image data product ID and file name.

    When adding a new PDS3-labeled survey to the service, edit this
    function so that it returns the correct image path.

    Parameters
    ----------
    label_path : str
        Path to the data label.

    Returns
    -------
    image_id : str
        Unique image identifier (PDS3 Product ID).

    image_path : str
        Full path to the image file.

    """

    try:
        label: PDS3Label = PDS3Label(label_path)
    except:
        raise InvalidPDS3Label(f'Error reading {label_path}')

    pointer: str
    if label['PRODUCT_NAME'] == "NEAT TRI-CAM IMAGE":
        pointer = '^IMAGE'
    else:
        pointer = '^IMAGE'

    image_path: str = os.path.join(
        os.path.dirname(label_path), label[pointer][0].lower())

    if not os.path.exists(image_path):
        # some of our archive is compressed
        image_path += '.fz'

    if not os.path.exists(image_path):
        raise InvalidImagePath(f'Could not find image in {label_path}.')

    return label['PRODUCT_ID'], image_path


def pds4_image(label_path: str) -> Tuple[str, str]:
    """Examine PDS3 label for image data product ID and file name.

    When adding a new PDS4-labeled survey to the service, edit this
    function so that it returns the correct image path.

    """

    raise InvalidPDS4Label()


def add_directory(path: str, session: Session, recursive: bool = False,
                  extensions: Optional[List[str]] = None) -> None:
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
                n_added += add_label(os.path.join(dirpath, filename), session)

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
    return parser.parse_args()


def _main() -> None:
    args: argparse.Namespace = _parse_args()

    session: Session
    with data_provider_session() as session:
        if args.create:
            Base.metadata.create_all(db_engine)

        for ld in args.labels_or_directories:
            if os.path.isdir(ld):
                add_directory(ld, session, recursive=args.r, extensions=args.e)
            else:
                add_label(ld, session)


if __name__ == '__main__':
    _main()
