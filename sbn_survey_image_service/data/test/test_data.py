# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Test services using test data set."""

import os
from tempfile import mkstemp
from .. import valid_pds3_label


def test_invalid_pds3_label():
    fd: int
    fn: str
    fd, fn = mkstemp()
    os.close(fd)
    with open(fn, 'w') as outf:
        outf.write('''\r
This is not a PDS3 label.\r
''')

    assert not valid_pds3_label(fn)

    os.unlink(fn)
