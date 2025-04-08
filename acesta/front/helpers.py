from django.conf import settings
from numpy.random import randint

from acesta.base.decorators import to_cache
from acesta.geo.models import Sight
from acesta.geo.models import SightGroup
from acesta.stats.models import RegionRating
from acesta.stats.models import SightRating


def get_random_tourism_type():
    """
    Returns a random tourism type
    :return: tuple
    """
    return settings.TOURISM_TYPES_OUTSIDE[randint(len(settings.TOURISM_TYPES_OUTSIDE))]


def get_random_sight_group():
    """
    Returns a random sight group
    :return: tuple
    """
    sight_group_name = sight_group = ""
    cnt = len(SightGroup.pub.all())
    if cnt:
        random_sight_group = SightGroup.pub.all()[randint(0, (cnt - 1) or 1)]
        sight_group_name = getattr(random_sight_group, "name")
        sight_group = getattr(random_sight_group, "title")
    return sight_group_name, sight_group


def get_top_regions(tourism_type: str, limit: int = 3):
    """
    Returns top regions by tourism_type
    :param tourism_type: str
    :param limit: int
    :return: django.db.models.QuerySet
    """

    @to_cache("regions_rating_{tourism_type}", 60 * 60 * 24 * 7)
    def get_regions_rating(**kwargs):
        return RegionRating.objects.filter(tourism_type=tourism_type).prefetch_related(
            "home_code"
        )[:limit]

    return get_regions_rating(tourism_type=tourism_type)


def get_top_sights(sight_group: str, limit: int = 3):
    """
    Returns top sights by sight_group
    :param sight_group: str
    :param limit: int
    :return: django.db.models.QuerySet
    """

    @to_cache("sights_cnt_{sight_group}", 60 * 60 * 24 * 7)
    def get_sights_rating(**kwargs):
        return SightRating.objects.filter(
            sight_group=sight_group, region_code__isnull=True
        ).prefetch_related("sight", "sight__code", "sight__city")[:limit]

    return get_sights_rating(sight_group=sight_group)


@to_cache("sights_cnt", 60 * 60 * 24 * 7)
def get_sights_cnt():
    """
    Returns quantity of sights
    :return: int
    """
    return Sight.pub.all().count()
