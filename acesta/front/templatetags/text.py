import re
from pathlib import Path

from django import template
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
from django.template import TemplateSyntaxError
from django.utils.safestring import mark_safe

register = template.Library()
OFFER_SVG_PATH = "img/offer.svg"


def _read_offer_svg():
    source_path = finders.find(OFFER_SVG_PATH)
    if source_path:
        return Path(source_path).read_text(encoding="utf-8")

    try:
        with staticfiles_storage.open(OFFER_SVG_PATH, "r") as source:
            svg = source.read()
    except (FileNotFoundError, OSError) as error:
        raise TemplateSyntaxError("Static offer SVG was not found") from error

    if isinstance(svg, bytes):
        return svg.decode("utf-8")
    return svg


@register.simple_tag
def inline_offer_svg():
    return mark_safe(_read_offer_svg())


@register.filter(is_safe=True)
def nobreak_spaces(value):
    if not isinstance(value, str):
        return value

    particles = [
        "из-за",
        "для",
        "через",
        "под",
        "при",
        "без",
        "во",
        "со",
        "об",
        "на",
        "за",
        "по",
        "из",
        "ее",
        "её",
        "от",
        "их",
        "до",
        "или",
        "не",
        "но",
        "то",
        "в",
        "и",
        "с",
        "к",
        "у",
        "о",
        "а",
        "да",
    ]

    pattern = re.compile(
        r"(\b)({})(\s+)".format("|".join(map(re.escape, particles))),
        flags=re.IGNORECASE,
    )

    result = pattern.sub(lambda m: m.group(1) + m.group(2) + "&nbsp;", value)

    result = re.sub(r"&nbsp;\s+", "&nbsp;", result)

    return mark_safe(result)
