import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass
from functools import lru_cache
from html import escape
from pathlib import Path
from urllib.parse import urlsplit

import qrcode
from django.conf import settings
from django.contrib.staticfiles import finders
from qrcode.constants import ERROR_CORRECT_H

MODULE_SIZE = 10
QUIET_ZONE_MODULES = 5
CAPTION_HEIGHT_MODULES = 14
CAPTION_FONT_SIZE_MODULES = 6.6


@dataclass(frozen=True)
class QRCode:
    svg: str
    url: str


def validate_qr_target(target_url: str | None) -> str:
    if not target_url:
        raise ValueError("QR target is required")
    target = target_url
    parts = urlsplit(target)
    if parts.scheme:
        if parts.scheme not in {"http", "https"} or not parts.netloc:
            raise ValueError("QR target must be an HTTP(S) URL or an internal path")
    elif not target.startswith("/") or target.startswith("//"):
        raise ValueError("QR target must be an HTTP(S) URL or an internal path")
    return target


def default_qr_caption(target_url: str) -> str:
    parts = urlsplit(target_url)
    if parts.netloc:
        return parts.netloc
    return settings.PUBLIC_DOMAIN


def generate_qr(
    target_url: str | None,
    *,
    caption: str | None = None,
    show_caption: bool = True,
) -> QRCode:
    target = validate_qr_target(target_url)
    if caption is None:
        caption = default_qr_caption(target)
    svg = render_rounded_qr_svg(
        target,
        caption=caption if show_caption else "",
    )
    return QRCode(svg=svg, url=target)


def render_rounded_qr_svg(data: str, *, caption: str = "") -> str:
    qr = qrcode.QRCode(
        error_correction=ERROR_CORRECT_H,
        box_size=1,
        border=0,
    )
    qr.add_data(data)
    qr.make(fit=True)
    matrix = qr.get_matrix()
    module_count = len(matrix)
    quiet = QUIET_ZONE_MODULES * MODULE_SIZE
    qr_size = module_count * MODULE_SIZE
    card_width = qr_size + quiet * 2
    caption_height = MODULE_SIZE * CAPTION_HEIGHT_MODULES if caption else quiet
    card_height = quiet + qr_size + caption_height

    finder_origins = (
        (0, 0),
        (module_count - 7, 0),
        (0, module_count - 7),
    )
    logo_modules = min(11, max(9, module_count // 6))
    if logo_modules % 2 == 0:
        logo_modules += 1
    logo_start = (module_count - logo_modules) // 2
    logo_end = logo_start + logo_modules

    modules = []
    radius = MODULE_SIZE * 0.38
    for row, values in enumerate(matrix):
        for column, enabled in enumerate(values):
            if not enabled:
                continue
            if _in_finder(column, row, finder_origins):
                continue
            if logo_start <= column < logo_end and logo_start <= row < logo_end:
                continue
            center_x = quiet + (column + 0.5) * MODULE_SIZE
            center_y = quiet + (row + 0.5) * MODULE_SIZE
            modules.append(
                f'<circle cx="{center_x:g}" cy="{center_y:g}" '
                f'r="{radius:g}" fill="#555354"/>'
            )

    finders = []
    for column, row in finder_origins:
        center_x = quiet + (column + 3.5) * MODULE_SIZE
        center_y = quiet + (row + 3.5) * MODULE_SIZE
        finders.append(
            f'<circle cx="{center_x:g}" cy="{center_y:g}" '
            f'r="{MODULE_SIZE * 3.5:g}" fill="#555354"/>'
            f'<circle cx="{center_x:g}" cy="{center_y:g}" '
            f'r="{MODULE_SIZE * 2.45:g}" fill="#fff"/>'
            f'<circle cx="{center_x:g}" cy="{center_y:g}" '
            f'r="{MODULE_SIZE * 1.45:g}" fill="#555354"/>'
        )

    logo_size = logo_modules * MODULE_SIZE * 0.88
    logo_x = (card_width - logo_size) / 2
    logo_y = quiet + (qr_size - logo_size) / 2
    logo = _render_logo_mark(logo_x, logo_y, logo_size)

    caption_svg = ""
    if caption:
        caption_y = quiet + qr_size + caption_height / 2
        font_size = min(
            MODULE_SIZE * CAPTION_FONT_SIZE_MODULES,
            card_width / max(len(caption) * 0.42, 1),
        )
        caption_svg = (
            f'<text x="{card_width / 2:g}" y="{caption_y:g}" '
            f'fill="#4b4a4a" font-family="Golos, sans-serif" '
            f'font-size="{font_size:g}" font-weight="500" text-anchor="middle" '
            f'dominant-baseline="middle">'
            f"{escape(caption)}</text>"
        )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {card_width} {card_height}" '
        f'role="img" aria-label="QR-код: {escape(caption or data)}">'
        f"<metadata>{escape(data)}</metadata>"
        f'<rect width="{card_width}" height="{card_height}" '
        f'rx="{MODULE_SIZE * 3}" fill="#fff" stroke="#fff" '
        f'stroke-opacity=".97" stroke-width="1"/>'
        f'{"".join(modules)}{"".join(finders)}{logo}{caption_svg}</svg>'
    )


def _in_finder(
    column: int,
    row: int,
    finder_origins: tuple[tuple[int, int], ...],
) -> bool:
    return any(
        origin_x <= column < origin_x + 7 and origin_y <= row < origin_y + 7
        for origin_x, origin_y in finder_origins
    )


@lru_cache(maxsize=1)
def _logo_mark_paths() -> tuple[tuple[str, str], ...]:
    logo_path = finders.find("img/qr/acesta-mark.svg")
    if not logo_path:
        raise FileNotFoundError("QR logo asset not found")
    root = ElementTree.parse(Path(logo_path)).getroot()
    namespace = "{http://www.w3.org/2000/svg}"
    paths = []
    for path in root.iter(f"{namespace}path"):
        fill = path.attrib.get("fill", "")
        if fill:
            paths.append((path.attrib["d"], fill))
    if not paths:
        raise ValueError("QR logo asset does not contain the colored mark")
    return tuple(paths)


def _render_logo_mark(x: float, y: float, size: float) -> str:
    mark_x = 0
    mark_y = 0
    mark_width = 45
    mark_height = 45
    scale = min(size / mark_width, size / mark_height)
    rendered_width = mark_width * scale
    rendered_height = mark_height * scale
    translate_x = x + (size - rendered_width) / 2 - mark_x * scale
    translate_y = y + (size - rendered_height) / 2 - mark_y * scale
    paths = "".join(
        f'<path d="{escape(path_data)}" fill="{fill}"/>'
        for path_data, fill in _logo_mark_paths()
    )
    return (
        f'<g transform="translate({translate_x:g} {translate_y:g}) '
        f'scale({scale:g})">{paths}</g>'
    )
