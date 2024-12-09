from django import template

from acesta.base.utils import timesince_accusatifier
from acesta.base.utils import timesince_cutter

register = template.Library()


@register.filter
def accusatifier(timesince_str) -> str:
    """
    Returns timesince in the accusative case
    :param timesince_str: str
    :return: str
    """
    return timesince_accusatifier(timesince_str)


@register.filter
def cutter(timesince_str) -> str:
    """
    Returns timesince in cut down format
    :param timesince_str: str
    :return: str
    """
    return timesince_cutter(timesince_str)
