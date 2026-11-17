from flask import send_file
from werkzeug.exceptions import BadGateway, BadRequest

from ..services.skymapper_preview import skymapper_preview


def get_preview(image: str, ra: float, dec: float, size: float):
    try:
        filename = skymapper_preview(image, ra, dec, size)
    except (ValueError, KeyError) as exc:
        raise BadRequest(str(exc)) from exc
    except Exception as exc:
        raise BadGateway("SkyMapper preview is temporarily unavailable") from exc
    return send_file(filename, mimetype="image/png", max_age=604800)
