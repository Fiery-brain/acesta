from django import template
from django.utils.safestring import mark_safe

from acesta.front.qr.generator import generate_qr

register = template.Library()


@register.simple_tag
def qr_svg(target_url, caption=None, show_caption=True):
    qr = generate_qr(
        target_url,
        caption=caption,
        show_caption=show_caption,
    )
    return mark_safe(qr.svg)
