import hashlib
import os
import time
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import BoundedSemaphore, Lock
from typing import Any

import requests
from astropy.io import fits
from astropy.wcs import WCS

from .owned_cutout_url import owned_cutout_url
from .survey_renderers import SurveyRenderers


class LocalPreviewService:
    """Bounded, lazy downloads and actual UMD renderers, with session-local files."""

    MAX_FITS_BYTES = 64 * 1024 * 1024
    MAX_PIXELS = 2048 * 2048

    def __init__(self, cache_directory: Path, renderers: SurveyRenderers):
        self.cache_directory = cache_directory
        self.renderers = renderers
        self.cache_directory.mkdir(parents=True, exist_ok=True)
        self._slots = BoundedSemaphore(2)
        self._locks: dict[str, Any] = {}
        self._locks_guard = Lock()
        self._completed: set[str] = set()

    def _lock(self, key: str):
        with self._locks_guard:
            return self._locks.setdefault(key, Lock())

    def owned_preview(self, source: str) -> tuple[Path, bool]:
        native, image_format = owned_cutout_url(source)
        digest = hashlib.sha256(native.encode()).hexdigest()
        science = self.cache_directory / (digest + ".fits")
        preview = self.cache_directory / (digest + ".north-up-v1." + image_format)
        destination = science if image_format == "fits" else preview
        # Lock before taking a worker slot: duplicates don't occupy both workers.
        with self._lock(native), self._slots:
            if destination.exists():
                return destination, True
            if not science.exists():
                self._download_science(native, science)
            if image_format != "fits":
                with fits.open(science, memmap=False) as hdus:
                    index = self._image_extension(hdus)
                self.renderers.create_browse_image(
                    str(science),
                    str(preview),
                    image_format,
                    True,
                    wcs_ext=index,
                    data_ext=index,
                )
            return destination, False

    def provider_preview(
        self, provider: str, params: dict[str, Any]
    ) -> tuple[Path, bool]:
        key = provider + repr(sorted(params.items()))
        renderer = {
            "skymapper": self.renderers.skymapper_preview,
            "panstarrs": self.renderers.panstarrs_preview,
        }[provider]
        with self._lock(key), self._slots:
            cached = key in self._completed
            filename = renderer(**params, cache_directory=str(self.cache_directory))
            self._completed.add(key)
            return Path(filename), cached

    @classmethod
    def _image_extension(cls, hdus: fits.HDUList) -> int:
        for index, hdu in enumerate(hdus):
            if not isinstance(hdu, (fits.PrimaryHDU, fits.ImageHDU, fits.CompImageHDU)):
                continue
            shape = hdu.shape
            if not shape or len(shape) != 2:
                continue
            height, width = shape
            if min(shape) < 1 or height * width > cls.MAX_PIXELS or max(shape) > 2048:
                raise ValueError(
                    "Local preview cutouts must be at most 2048 by 2048 pixels"
                )
            header = hdu.header.copy()
            header.remove("XPIXELSZ", ignore_missing=True)
            header.remove("YPIXELSZ", ignore_missing=True)
            if WCS(header).has_celestial:
                return index
        raise ValueError(
            "Native cutout contains no two-dimensional image with celestial WCS"
        )

    def _download_science(self, url: str, destination: Path) -> None:
        started = time.monotonic()
        temporary = None
        try:
            with requests.get(
                url, stream=True, timeout=(10, 30), allow_redirects=False
            ) as response:
                response.raise_for_status()
                if response.status_code != 200:
                    raise ValueError("Expected a complete native FITS cutout")
                length = response.headers.get("Content-Length")
                if length and int(length) > self.MAX_FITS_BYTES:
                    raise ValueError(
                        "Native cutout exceeds the local 64 MiB download limit"
                    )
                with NamedTemporaryFile(
                    dir=self.cache_directory, suffix=".fits", delete=False
                ) as output:
                    temporary = Path(output.name)
                    size = 0
                    for chunk in response.iter_content(512 * 1024):
                        size += len(chunk)
                        if (
                            size > self.MAX_FITS_BYTES
                            or time.monotonic() - started > 40
                        ):
                            raise ValueError(
                                "Native cutout exceeds the local download budget"
                            )
                        output.write(chunk)
            with fits.open(temporary, memmap=False) as hdus:
                self._image_extension(hdus)
            os.replace(temporary, destination)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
