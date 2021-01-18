# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""App exceptions."""


class SBNSISException(Exception):
    """Generic SBN Survey Image Service exception."""


class InvalidImageID(SBNSISException):
    """Image ID is not in database."""


class InvalidImagePath(SBNSISException):
    """Image path is invalid."""


class InvalidLabel(SBNSISException):
    """File is not a valid PDS label."""


class InvalidPDS3Label(InvalidLabel):
    """File is not a valid PDS3 label."""


class InvalidPDS4Label(InvalidLabel):
    """File is not a valid PDS4 label."""


class BadPixelScale(SBNSISException):
    """Bad pixel scale."""


class ParameterValueError(SBNSISException):
    """Parameter value error."""
