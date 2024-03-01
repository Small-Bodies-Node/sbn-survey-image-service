# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""App exceptions.

Classes intended to be caught by the API app are annotated with HTTP status
codes.

"""


class SBNSISException(Exception):
    """Generic SBN Survey Image Service exception."""


class InvalidImageID(SBNSISException):
    """Image ID is not in database."""

    code = 404


class InvalidImageURL(SBNSISException):
    """Image URL is invalid."""


class LabelError(SBNSISException):
    """File is not a valid PDS label."""


class PDS4LabelError(LabelError):
    """Error while attempting to read PDS4 label."""


class BadPixelScale(SBNSISException):
    """Bad pixel scale."""


class ParameterValueError(SBNSISException):
    """Parameter value error."""

    code = 400


class FitscutError(SBNSISException):
    """Error processing data with fitscut."""

    code = 500


class DatabaseError(SBNSISException):
    """Database error."""

    code = 500


class SBNSISWarning(SBNSISException):
    """Warnings."""


class InvalidNEATImage(SBNSISWarning):
    """Invalid NEAT survey image."""


class InvalidATLASImage(SBNSISWarning):
    """Invalid NEAT survey image."""
