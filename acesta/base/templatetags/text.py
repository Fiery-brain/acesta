import re

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(is_safe=True)
def nobreak_spaces(value):
    if not isinstance(value, str):
        return value

    particles = [
        "в",
        "и",
        "с",
        "к",
        "у",
        "о",
        "на",
        "за",
        "по",
        "из",
        "от",
        "до",
        "не",
        "но",
        "а",
        "да",
        "или",
        "из-за",
        "то",
    ]

    pattern = re.compile(
        r"(\b)({})(\s+)".format("|".join(map(re.escape, particles))),
        flags=re.IGNORECASE,
    )

    result = pattern.sub(lambda m: m.group(1) + m.group(2) + "&nbsp;", value)

    result = re.sub(r"&nbsp;\s+", "&nbsp;", result)

    return mark_safe(result)
