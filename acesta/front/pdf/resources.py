from pathlib import Path
from urllib.parse import unquote
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.staticfiles import finders


def resolve_local_resource(url: str) -> Path | None:
    """Resolve a local static or media URL without making an HTTP request."""
    path = unquote(urlsplit(url).path)

    if path.startswith(settings.STATIC_URL):
        relative_path = path.removeprefix(settings.STATIC_URL).lstrip("/")
        if not _is_safe_relative_path(relative_path):
            raise ValueError(f"Unsafe static resource path: {path}")

        static_root = Path(settings.STATIC_ROOT).resolve()
        collected_path = (static_root / relative_path).resolve()
        if not collected_path.is_relative_to(static_root):
            raise ValueError(f"Unsafe static resource path: {path}")
        if collected_path.is_file():
            return collected_path

        resolved_path = finders.find(relative_path)
        if not resolved_path:
            raise FileNotFoundError(f"Static resource not found: {path}")
        return Path(resolved_path)

    if path.startswith(settings.MEDIA_URL):
        relative_path = path.removeprefix(settings.MEDIA_URL).lstrip("/")
        if not _is_safe_relative_path(relative_path):
            raise ValueError(f"Unsafe media resource path: {path}")
        media_root = Path(settings.MEDIA_ROOT).resolve()
        resolved_path = (media_root / relative_path).resolve()
        if not resolved_path.is_relative_to(media_root):
            raise ValueError(f"Unsafe media resource path: {path}")
        if not resolved_path.is_file():
            raise FileNotFoundError(f"Media resource not found: {path}")
        return resolved_path

    return None


def _is_safe_relative_path(path: str) -> bool:
    candidate = Path(path)
    return bool(path) and not candidate.is_absolute() and ".." not in candidate.parts
