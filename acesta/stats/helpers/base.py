import math

from acesta.base.decorators import to_cache
from acesta.geo.models import Region


@to_cache("regions_cnt", 60 * 60 * 24 * 7)
def get_regions_cnt():
    """
    Returns quantity of regions
    :return: int
    """
    return Region.pub.all().count()


def formatted_percentage(x: int, y: int) -> str:
    """
    Returns formatted result
    :return: str
    """
    try:
        return str(int(round(x / y, 2) * 100)).rjust(2)
    except ZeroDivisionError:
        return "0"


def round_up(n, decimals=0) -> int:
    """
    Rounds number up to thousands
    :param n: int
    :param decimals: int
    :return: int
    """
    multiplier = 10**decimals
    return math.ceil(n * multiplier) / multiplier
