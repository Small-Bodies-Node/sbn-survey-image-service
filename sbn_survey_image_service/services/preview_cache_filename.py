import hashlib
from pathlib import Path


def preview_cache_filename(*parts: str, cache_directory: str | None = None) -> str:
    """Use the application cache normally, or an explicitly isolated development cache."""
    if cache_directory is None:
        from ..data import generate_cache_filename

        return generate_cache_filename(*parts)
    digest = hashlib.sha256(repr(parts).encode()).hexdigest()
    return str(Path(cache_directory) / digest)
