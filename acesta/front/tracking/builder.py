from collections.abc import Mapping
from urllib.parse import parse_qsl
from urllib.parse import urlencode
from urllib.parse import urlsplit
from urllib.parse import urlunsplit


def build_tracking_url(
    target_url: str | None,
    *,
    source: str | None,
    medium: str | None,
    campaign: str | None,
    content: str | None,
    dimensions: Mapping[str, str | None] | None = None,
) -> str:
    """Add UTM attribution and optional dimensions to an arbitrary URL."""
    if not target_url:
        raise ValueError("Tracking target URL is required")

    parts = urlsplit(target_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    tracking_dimensions = {
        "utm_source": source,
        "utm_medium": medium,
        "utm_campaign": campaign,
        "utm_content": content,
    }
    tracking_dimensions.update(dimensions or {})
    for key, value in tracking_dimensions.items():
        if value:
            query[key] = value
        else:
            query.pop(key, None)

    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(query),
            parts.fragment,
        )
    )
