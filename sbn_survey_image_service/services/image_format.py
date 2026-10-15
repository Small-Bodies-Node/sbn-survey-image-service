from enum import Enum


class ImageFormat(Enum):
    # parameter, Pillow Image format, file extension
    FITS = ("fits", "fits", "fits")
    JPEG = ("jpeg", "jpeg", "jpeg")
    JPG = ("jpg", "jpeg", "jpeg")
    PNG = ("png", "png", "png")
    DEFAULT = (None, "fits", "fits")

    def __new__(cls, parameter, format, extension):
        self = object.__new__(cls)
        self._value_ = parameter
        self.format = format
        self.extension = extension
        return self
