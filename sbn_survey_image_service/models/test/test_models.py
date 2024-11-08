# Licensed under a 3-clause BSD style license - see LICENSE.rst

from ..image import Image


class TestImage:
    """Test Image object odds and ends."""

    def test_repr(self):
        im: Image = Image(obs_id="asdf", image_url="fdsa", label_url="jkl;")
        assert repr(im) == "Image(obs_id='asdf', image_url='fdsa', label_url='jkl;')"

    def test_str(self):
        im: Image = Image(obs_id="asdf", image_url="fdsa", label_url="jkl;")
        assert str(im) == "<Class Image: asdf>"
