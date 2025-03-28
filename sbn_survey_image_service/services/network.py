"""
Set HTTP User-Agent parameter.
"""

from contextlib import contextmanager
import requests as req
from astropy.utils.data import conf as astropy_conf
from .. import __version__


user_agent = f"SBN Survey Image Service {__version__}"


@contextmanager
def session():
    with req.Session() as s:
        s.headers.update({"User-Agent": user_agent})
        yield s


@contextmanager
def set_astropy_useragent():
    with astropy_conf.set_temp("default_http_user_agent", user_agent):
        yield
