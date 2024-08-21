# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Data functions."""

__all__ = ["url_to_local_file", "generate_cache_filename"]

import io
import os
import hashlib
import requests
from requests.models import HTTPError
from urllib.parse import ParseResult, urlparse

from ..config.env import ENV


def url_to_local_file(url: str) -> str:
    """Returns path to a local file, fetching remote files as needed."""
    path: str
    p: ParseResult = urlparse(url)
    if p.scheme == "file":
        path = os.path.abspath(p.path)
    else:
        r: requests.Response = requests.get(url)
        if r.status_code != 200:
            raise HTTPError(r.status_code)

        path = generate_cache_filename(url)
        outf: io.IOBase
        with open(path, "wb") as outf:
            outf.write(r.content)

        # rw-rw-r--
        # In [16]: (stat.S_IFREG | stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)
        # Out[16]: 33204
        os.chmod(path, 33204)

    return path


def generate_cache_filename(*args):
    """Make consistent file name based on MD5 sum of the arguments.


    Parameters
    ----------
    *args : strings
        Order is important.

    """

    m = hashlib.md5()
    m.update("".join(args).encode())
    return os.path.join(ENV.SBNSIS_CUTOUT_CACHE, m.hexdigest())
