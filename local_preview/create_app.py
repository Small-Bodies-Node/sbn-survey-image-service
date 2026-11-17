from pathlib import Path

from flask import Flask, jsonify, request, send_file
from werkzeug.exceptions import BadGateway, BadRequest

from .load_survey_renderers import load_survey_renderers
from .local_preview_service import LocalPreviewService


def create_app(cache_directory: Path) -> Flask:
    """A local-only API for previews; it never initializes the catalogue database."""
    app = Flask(__name__)
    service = LocalPreviewService(cache_directory, load_survey_renderers())
    app.extensions["local_preview_service"] = service

    @app.after_request
    def local_headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-CATCH-Image-Renderer"] = "north-up-v1"
        response.headers["X-CATCH-Image-Mode"] = "local"
        return response

    @app.get("/health")
    def health():
        return jsonify(
            mode="local-preview", renderer="north-up-v1", cache=str(cache_directory)
        )

    def preview_response(callback):
        try:
            filename, cached = callback()
        except (ValueError, KeyError, TypeError) as error:
            raise BadRequest(str(error)) from error
        except Exception as error:
            app.logger.exception("Local preview generation failed")
            raise BadGateway(
                "Local preview generation failed; check the renderer log"
            ) from error
        mimetype = (
            "application/fits"
            if filename.suffix == ".fits"
            else ("image/jpeg" if filename.suffix == ".jpeg" else "image/png")
        )
        response = send_file(filename, mimetype=mimetype, conditional=True)
        response.headers["X-CATCH-Image-Cache"] = "hit" if cached else "miss"
        return response

    @app.get("/images/owned")
    def owned():
        return preview_response(
            lambda: service.owned_preview(request.args.get("url", ""))
        )

    @app.get("/previews/<provider>")
    def external(provider: str):
        if provider not in ("skymapper", "panstarrs"):
            return jsonify(error="Unknown preview provider"), 404
        try:
            params = {
                "image": request.args["image"],
                "ra": float(request.args["ra"]),
                "dec": float(request.args["dec"]),
                "size": float(request.args["size"]),
            }
            if provider == "panstarrs":
                if not params["size"].is_integer():
                    raise ValueError("Pan-STARRS size must be an integer")
                params["size"] = int(params["size"])
        except (ValueError, KeyError) as error:
            raise BadRequest("Expected image, ra, dec and size parameters") from error
        return preview_response(lambda: service.provider_preview(provider, params))

    return app
