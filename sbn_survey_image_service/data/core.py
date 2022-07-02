# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Data functions."""

__all__ = [
    'valid_pds3_label',
    'url_to_local_file'
]

import io
import os
from tempfile import mkstemp
import requests
from requests.models import HTTPError
from urllib.parse import ParseResult, urlparse

from ..env import ENV


def valid_pds3_label(filename: str) -> bool:
    """Test that this is probably a PDS3 label."""

    inf: io.IOBase
    with open(filename, 'r', newline='\r\n') as inf:
        # read at most 100 lines, looking for PDS_VERSION_ID
        n: int = 0
        line: str = ''
        for line in inf:
            n += 1
            if line.strip() == '':
                continue
            if line.strip().replace(' ', '') == 'PDS_VERSION_ID=PDS3':
                return True
        return False


def url_to_local_file(url: str, uncompress: bool = True) -> str:
    """Returns path to a local file, fetching remote files as needed."""
    path: str
    p: ParseResult = urlparse(url)
    if p.scheme == 'file':
        path = os.path.abspath(p.path)
    else:
        r: requests.Response = requests.get(url)
        if r.status_code != 200:
            raise HTTPError(r.status_code)

        fd: int
        #text: bool = r.headers.get('Content-Type', '').startswith('text')
        fd, path = mkstemp(dir=ENV.SBNSIS_CUTOUT_CACHE)
        outf: io.IOBase
        with open(fd, 'wb') as outf:
            outf.write(r.content)

        # rw-rw-r--
        # In [16]: (stat.S_IFREG | stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)
        # Out[16]: 33204
        os.chmod(path, 33204)

    # uncompress as needed

    return path
