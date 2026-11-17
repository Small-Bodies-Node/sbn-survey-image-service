import importlib
import sys
from pathlib import Path
from types import ModuleType

from .survey_renderers import SurveyRenderers


def load_survey_renderers() -> SurveyRenderers:
    """Load the real renderer source without the app's .env/database bootstrap.

    The legacy top-level package initializes global deployment configuration on
    import. A private namespace lets this harness reuse its pure service modules
    unchanged; cache paths are passed explicitly. No renderer is reimplemented.
    """
    root = Path(__file__).resolve().parents[1] / "sbn_survey_image_service"
    package = "_catch_local_survey"
    for name, directory in [
        (package, root),
        (package + ".services", root / "services"),
    ]:
        if name not in sys.modules:
            module = ModuleType(name)
            module.__path__ = [str(directory)]
            sys.modules[name] = module
    return SurveyRenderers(
        importlib.import_module(
            package + ".services.create_browse_image"
        ).create_browse_image,
        importlib.import_module(
            package + ".services.skymapper_preview"
        ).skymapper_preview,
        importlib.import_module(
            package + ".services.panstarrs_preview"
        ).panstarrs_preview,
    )
