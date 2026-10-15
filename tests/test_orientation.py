import importlib.util
import io
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import astropy.units as u
import numpy as np
import pytest
from astropy.io import fits
from astropy.wcs import WCS
from PIL import Image
from pyavm import AVM

ROOT = Path(__file__).parents[1] / "sbn_survey_image_service"
PACKAGE = "_orientation_service"
for name, directory in [(PACKAGE, ROOT), (PACKAGE + ".services", ROOT / "services")]:
    module = ModuleType(name)
    module.__path__ = [str(directory)]
    sys.modules[name] = module


def load(name):
    spec = importlib.util.spec_from_file_location(
        PACKAGE + ".services." + name, ROOT / "services" / (name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


north_up = load("north_up_wcs").north_up_wcs
sky = load("skymapper_preview")
ps1 = load("panstarrs_preview")
render_browse = load("create_browse_image").create_browse_image


@pytest.mark.parametrize("angle,parity", [(0, -1), (31, -1), (180, -1), (31, 1)])
def test_rectangular_rotated_and_mirrored_wcs(angle, parity):
    native = WCS(naxis=2)
    native.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    native.wcs.crval = [344.3, -16.2]
    native.wcs.crpix = [-140, 260]
    r = np.deg2rad(angle)
    native.wcs.cd = np.array(
        [[np.cos(r), -np.sin(r)], [np.sin(r), np.cos(r)]]
    ) @ np.diag([parity * 0.00014, 0.00014])
    target = north_up(native, (33, 57))
    assert target.pixel_shape == (57, 33)
    np.testing.assert_allclose(target.wcs.crpix, [29, 17])
    center = target.pixel_to_world(28, 16)
    assert center.icrs.separation(native.pixel_to_world(28, 16).icrs).arcsec < 1e-6
    n = target.world_to_pixel(center.directional_offset_by(0 * u.deg, 10 * u.arcsec))
    e = target.world_to_pixel(center.directional_offset_by(90 * u.deg, 10 * u.arcsec))
    assert abs(n[0] - 28) < 1e-5 and n[1] > 16
    assert abs(e[1] - 16) < 1e-5 and e[0] < 28


class Reply:
    def __init__(self, data, status=206, range_value="bytes 0-2879/28800"):
        self.raw = io.BytesIO(data)
        self.status_code = status
        self.headers = {"Content-Range": range_value}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_header_stops_at_end_without_scientific_pixels():
    encoded = fits.PrimaryHDU(np.zeros((33, 57))).header.tostring().encode()
    session = MagicMock()
    session.get.return_value = Reply(encoded[:2880])
    header = sky.read_fits_header(sky.SKYMAPPER_URL, {}, session)
    assert header["NAXIS1"] == 57 and header["NAXIS2"] == 33
    assert session.get.call_count == 1
    assert session.get.call_args.kwargs["headers"]["Range"] == "bytes=0-2879"


@pytest.mark.parametrize(
    "status,range_value,data",
    [
        (200, "", b" " * 2880),
        (206, "bytes 1-2880/28800", b" " * 2880),
        (206, "bytes 0-2879/28800", b" " * 2879),
    ],
)
def test_rejects_full_downloads_or_incorrect_ranges(status, range_value, data):
    session = MagicMock()
    session.get.return_value = Reply(data, status, range_value)
    with pytest.raises(ValueError):
        sky.read_fits_header(sky.SKYMAPPER_URL, {}, session)


def test_reported_skymapper_tpv_cutout_roundtrips():
    header = fits.Header.fromtextfile(
        Path(__file__).parent / "data" / "skymapper-20180516174436-12.hdr"
    )
    native = WCS(header)
    target = north_up(native, (header["NAXIS2"], header["NAXIS1"]))
    xx, yy = np.meshgrid([0, 140, 287.5, 430, 575], [0, 151, 302.5, 450, 605])
    display = target.world_to_pixel(native.pixel_to_world(xx, yy))
    original = native.world_to_pixel(target.pixel_to_world(*display))
    np.testing.assert_allclose(original[0], xx, atol=1e-6)
    np.testing.assert_allclose(original[1], yy, atol=1e-6)


@pytest.mark.parametrize("format", ["jpeg", "png"])
def test_actual_browse_renderer_embeds_rectangular_output_geometry(tmp_path, format):
    header = fits.Header.fromtextfile(
        Path(__file__).parent / "data" / "skymapper-20180516174436-12.hdr"
    )
    yy, xx = np.mgrid[: header["NAXIS2"], : header["NAXIS1"]]
    data = np.exp(-((xx - 287.5) ** 2 + (yy - 302.5) ** 2) / 4)
    science = tmp_path / "science.fits"
    fits.PrimaryHDU(data, header).writeto(science)
    original = science.read_bytes()
    preview = tmp_path / ("preview." + format)
    render_browse(str(science), str(preview), format, True)
    assert Image.open(preview).size == (576, 606)
    assert science.read_bytes() == original
    target = AVM.from_image(str(preview)).to_wcs()
    native = WCS(header)
    assert (
        target.pixel_to_world(287.5, 302.5)
        .icrs.separation(native.pixel_to_world(287.5, 302.5).icrs)
        .arcsec
        < 1e-5
    )
    assert target.wcs.cdelt[0] < 0 and target.wcs.cdelt[1] > 0


@pytest.mark.parametrize("pa", [0, 180])
def test_skymapper_png_transform_uses_matching_fits_header(tmp_path, monkeypatch, pa):
    header = fits.Header.fromtextfile(
        Path(__file__).parent / "data" / "skymapper-20180516174436-12.hdr"
    )
    header["ROTSKYPA"] = pa
    if pa == 180:
        for key in ["CD1_1", "CD1_2", "CD2_1", "CD2_2"]:
            header[key] = -header[key]
    yy, xx = np.mgrid[:606, :576]
    native = ((3 * xx + 5 * yy) % 250).astype(np.uint8)
    upstream = native[::-1]
    if pa == 180:
        upstream = upstream[::-1, ::-1]
    encoded = io.BytesIO()
    Image.fromarray(upstream).save(encoded, format="PNG")
    reply = Reply(b"")
    reply.raw = SimpleNamespace(read=lambda *args, **kwargs: encoded.getvalue())
    reply.raise_for_status = lambda: None
    monkeypatch.setattr(sky.requests, "get", lambda *args, **kwargs: reply)
    monkeypatch.setattr(sky, "read_fits_header", lambda *args, **kwargs: header)
    cache = ModuleType(PACKAGE + ".data")
    cache.generate_cache_filename = lambda *args: str(tmp_path / "cached.png")
    monkeypatch.setitem(sys.modules, PACKAGE + ".data", cache)
    path = sky.skymapper_preview("20180516174436-12", 344.31182, -16.20253, 0.0833)
    target = AVM.from_image(path).to_wcs()
    nx, ny = WCS(header).world_to_pixel(target.pixel_to_world(288, 303))
    assert (
        np.asarray(Image.open(path))[302, 288]
        == native[int(np.floor(ny + 0.5)), int(np.floor(nx + 0.5))]
    )


def test_panstarrs_reads_only_the_exact_cutout_header(tmp_path, monkeypatch):
    native_wcs = WCS(naxis=2)
    native_wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    native_wcs.wcs.crval = [85.714, 22]
    native_wcs.wcs.crpix = [-27730, -320]
    native_wcs.wcs.cdelt = [-1 / 14400, 1 / 14400]
    native_wcs.wcs.radesys = "ICRS"
    yy, xx = np.mgrid[:120, :120]
    pixels = ((3 * xx + 5 * yy) % 250).astype(np.uint8)
    header = fits.PrimaryHDU(pixels, native_wcs.to_header()).header.tostring().encode()
    fits_reply = Reply(header + b"UNREAD SCIENTIFIC PIXELS", status=200)
    fits_reply.raise_for_status = lambda: None
    png = io.BytesIO()
    Image.fromarray(pixels[::-1]).save(png, format="PNG")
    png_reply = Reply(b"")
    png_reply.raw = SimpleNamespace(read=lambda *args, **kwargs: png.getvalue())
    png_reply.raise_for_status = lambda: None
    requests_mock = MagicMock(side_effect=[fits_reply, png_reply])
    monkeypatch.setattr(ps1.requests, "get", requests_mock)
    cache = ModuleType(PACKAGE + ".data")
    cache.generate_cache_filename = lambda *args: str(tmp_path / "ps1.png")
    monkeypatch.setitem(sys.modules, PACKAGE + ".data", cache)
    result = ps1.panstarrs_preview(
        "/rings.v3.skycell/1784/059/rings.v3.skycell.1784.059.wrp.g.55560_46188.fits",
        83.6333,
        22.0133,
        120,
    )
    assert fits_reply.raw.tell() == len(header)
    assert requests_mock.call_count == 2
    assert (
        requests_mock.call_args_list[0].kwargs["params"]["size"]
        == requests_mock.call_args_list[1].kwargs["params"]["size"]
    )
    target = AVM.from_image(result).to_wcs()
    assert (
        target.pixel_to_world(59.5, 59.5)
        .separation(native_wcs.pixel_to_world(59.5, 59.5))
        .arcsec
        < 1e-5
    )
    assert target.wcs.cdelt[0] < 0 < target.wcs.cdelt[1]
