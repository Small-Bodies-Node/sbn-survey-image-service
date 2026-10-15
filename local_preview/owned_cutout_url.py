import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def owned_cutout_url(source: str) -> tuple[str, str]:
    """Validate a public owned endpoint and identify its unchanged native FITS cutout."""
    url = urlsplit(source)
    owned = url.hostname == "sbnsurveys.astro.umd.edu" or re.fullmatch(
        r"uxzqjwo0ye\.execute-api\.[a-z0-9-]+\.amazonaws\.com", url.hostname or ""
    )
    if (
        url.scheme != "https"
        or not owned
        or url.username
        or url.password
        or url.port not in (None, 443)
        or not url.path.startswith("/api/images/")
        or len(source) > 8192
    ):
        raise ValueError("Expected a public HTTPS UMD/AWS image cutout URL")
    params = dict(parse_qsl(url.query, keep_blank_values=True))
    image_format = params.get("format", "").lower()
    if image_format not in ("fits", "jpeg", "jpg", "png"):
        raise ValueError("Expected FITS, JPEG or PNG format")
    # Browses and science share one download, independent of renderer/cache hints.
    params.pop("align", None)
    params.pop("renderer", None)
    params["format"] = "fits"
    native = urlunsplit(
        ("https", url.netloc, url.path, urlencode(sorted(params.items())), "")
    )
    return native, "jpeg" if image_format == "jpg" else image_format
