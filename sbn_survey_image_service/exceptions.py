# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""App exceptions."""


class SBNSISException(Exception):
    """Generic SBN Survey Image Service exception."""


class InvalidImageID(SBNSISException):
    """Image ID is not in database."""


class InvalidImagePath(SBNSISException):
    """Image path is invalid."""


class LabelError(SBNSISException):
    """File is not a valid PDS label."""


class PDS3LabelError(LabelError):
    """Error while attempting to read PDS3 label."""


class PDS4LabelError(LabelError):
    """Error while attempting to read PDS4 label."""


class BadPixelScale(SBNSISException):
    """Bad pixel scale."""


class ParameterValueError(SBNSISException):
    """Parameter value error."""


class SBNSISWarning(SBNSISException):
    """Warnings."""


class InvalidNEATImage(SBNSISWarning):
    """Invalid NEAT survey image."""
