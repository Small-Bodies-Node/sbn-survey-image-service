import io
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import MagicMock

import astropy.units as u
import numpy as np
import pytest
from astropy.io import fits
from astropy.wcs import WCS
from PIL import Image
from pyavm import AVM

from local_preview.create_app import create_app
from local_preview.load_survey_renderers import load_survey_renderers
from local_preview.local_preview_service import LocalPreviewService
from local_preview.owned_cutout_url import owned_cutout_url

SOURCE = "https://sbnsurveys.astro.umd.edu/api/images/example?ra=10&dec=20&size=5arcmin&format=jpeg"


@pytest.fixture
def native():
    wcs = WCS(naxis=2)
    wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    wcs.wcs.crval = [10, 20]
    wcs.wcs.crpix = [16, 11]
    angle = np.deg2rad(35)
    wcs.wcs.cd = np.array(
        [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]]
    ) @ np.diag([0.001, 0.001])
    pixels = np.arange(20 * 30, dtype=np.float32).reshape(20, 30)
    output = io.BytesIO()
    fits.PrimaryHDU(pixels, wcs.to_header()).writeto(output)
    return output.getvalue()


def mock_download(monkeypatch, native):
    response = MagicMock()
    response.__enter__.return_value = response
    response.status_code = 200
    response.headers = {"Content-Length": str(len(native))}
    response.iter_content.return_value = [native]
    get = MagicMock(return_value=response)
    monkeypatch.setattr("local_preview.local_preview_service.requests.get", get)
    return get


def test_owned_preview_and_science_reuse_one_unchanged_download(
    tmp_path, native, monkeypatch
):
    get = mock_download(monkeypatch, native)
    app = create_app(tmp_path)
    client = app.test_client()
    browse = client.get("/images/owned", query_string={"url": SOURCE})
    assert browse.status_code == 200 and browse.mimetype == "image/jpeg"
    assert browse.headers["Cache-Control"] == "no-store"
    assert browse.headers["X-CATCH-Image-Mode"] == "local"
    assert browse.headers["X-CATCH-Image-Cache"] == "miss"
    science = client.get(
        "/images/owned",
        query_string={"url": SOURCE.replace("format=jpeg", "format=fits")},
    )
    assert science.status_code == 200 and science.data == native
    assert science.headers["X-CATCH-Image-Cache"] == "hit"
    again = client.get(
        "/images/owned",
        query_string={"url": SOURCE + "&renderer=north-up-v1&align=true"},
    )
    assert again.data == browse.data and again.headers["X-CATCH-Image-Cache"] == "hit"
    assert get.call_count == 1
    assert "format=fits" in get.call_args.args[0]
    assert get.call_args.kwargs["allow_redirects"] is False

    preview = next(tmp_path.glob("*.jpeg"))
    assert Image.open(preview).size == (30, 20)
    target = AVM.from_image(str(preview)).to_wcs()
    center = target.pixel_to_world(14.5, 9.5)
    north = target.world_to_pixel(center.directional_offset_by(0 * u.deg, 1 * u.arcsec))
    east = target.world_to_pixel(center.directional_offset_by(90 * u.deg, 1 * u.arcsec))
    assert north[1] > 9.5 and east[0] < 14.5


def test_simultaneous_owned_requests_share_the_download_and_render(
    tmp_path, native, monkeypatch
):
    get = mock_download(monkeypatch, native)
    service = LocalPreviewService(tmp_path, load_survey_renderers())
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(service.owned_preview, [SOURCE] * 4))
    assert get.call_count == 1
    assert sum(not cached for _, cached in results) == 1
    assert len({path for path, _ in results}) == 1


@pytest.mark.parametrize(
    "source",
    [
        "http://sbnsurveys.astro.umd.edu/api/images/id?format=fits",
        "https://sbnsurveys.astro.umd.edu.attacker.example/api/images/id?format=fits",
        "https://user:password@sbnsurveys.astro.umd.edu/api/images/id?format=fits",
        "https://sbnsurveys.astro.umd.edu:1234/api/images/id?format=fits",
        "https://sbnsurveys.astro.umd.edu/api/labels/id?format=fits",
        "https://sbnsurveys.astro.umd.edu/api/images/id?format=label",
        "https://127.0.0.1/api/images/id?format=fits",
    ],
)
def test_rejects_non_image_urls_before_any_download(tmp_path, monkeypatch, source):
    get = MagicMock()
    monkeypatch.setattr("local_preview.local_preview_service.requests.get", get)
    response = (
        create_app(tmp_path)
        .test_client()
        .get("/images/owned", query_string={"url": source})
    )
    assert response.status_code == 400
    get.assert_not_called()


def test_oversized_download_leaves_no_science_or_preview(tmp_path, native, monkeypatch):
    get = mock_download(monkeypatch, native)
    get.return_value.headers["Content-Length"] = str(
        LocalPreviewService.MAX_FITS_BYTES + 1
    )
    response = (
        create_app(tmp_path)
        .test_client()
        .get("/images/owned", query_string={"url": SOURCE})
    )
    assert response.status_code == 400
    assert list(tmp_path.iterdir()) == []


def test_external_adapter_receives_explicit_cache_and_exact_cutout_params(
    tmp_path, monkeypatch
):
    renderers = load_survey_renderers()
    image = tmp_path / "result.png"
    Image.new("L", (30, 20)).save(image)
    renderer = MagicMock(return_value=str(image))
    monkeypatch.setattr(
        "local_preview.create_app.load_survey_renderers",
        lambda: type(renderers)(renderers.create_browse_image, renderer, renderer),
    )
    client = create_app(tmp_path).test_client()
    params = {
        "image": "20180516174436-12",
        "ra": "344.31182",
        "dec": "-16.20253",
        "size": "0.0833",
    }
    response = client.get("/previews/skymapper", query_string=params)
    assert response.status_code == 200 and response.mimetype == "image/png"
    renderer.assert_called_once_with(
        image=params["image"],
        ra=344.31182,
        dec=-16.20253,
        size=0.0833,
        cache_directory=str(tmp_path),
    )
    assert (
        client.get(
            "/previews/panstarrs", query_string={**params, "size": "720.5"}
        ).status_code
        == 400
    )
    assert client.get("/previews/unknown", query_string=params).status_code == 404


def test_browse_hints_do_not_change_the_native_cache_identity():
    assert (
        owned_cutout_url(SOURCE)[0]
        == owned_cutout_url(SOURCE + "&align=true&renderer=north-up-v1")[0]
    )
    native, image_format = owned_cutout_url(
        SOURCE.replace(
            "sbnsurveys.astro.umd.edu", "uxzqjwo0ye.execute-api.us-west-1.amazonaws.com"
        )
    )
    assert image_format == "jpeg" and "format=fits" in native
