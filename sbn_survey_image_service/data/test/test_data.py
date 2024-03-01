# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Test services using test data set."""

import os
from tempfile import mkstemp
import pytest
import numpy as np
from astropy.io import fits
from .. import url_to_local_file


@pytest.mark.remote_data
def test_url_to_local_file_http_binary():
    fn: str = url_to_local_file(
        "https://sbnarchive.psi.edu/pds4/surveys/gbo.ast.neat.survey/"
        "data_tricam/p20011122/obsdata/20011122022445d.fit.fz"
    )
    assert np.isclose(fits.getdata(fn)[0, 0], 441.1902)


@pytest.mark.remote_data
def test_url_to_local_file_http_text():
    fn: str = url_to_local_file(
        "https://sbnarchive.psi.edu/pds4/surveys/gbo.ast.neat.survey/"
        "data_tricam/p20011122/obsdata/20011122022445d.xml"
    )
    with open(fn, "r") as inf:
        assert inf.readline().strip() == '<?xml version="1.0" encoding="UTF-8"?>'


def test_url_to_local_file_local_path():
    fd: int
    fn: str
    fd, fn = mkstemp()
    with open(fd, "w") as outf:
        outf.write("asdf")

    fn = url_to_local_file("file://" + os.path.abspath(fn))
    assert open(fn, "r").read() == "asdf"
