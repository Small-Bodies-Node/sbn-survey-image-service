from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class SurveyRenderers:
    create_browse_image: Callable[..., None]
    skymapper_preview: Callable[..., str]
    panstarrs_preview: Callable[..., str]
