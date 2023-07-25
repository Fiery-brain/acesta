from django.conf import settings
from django.core.cache import caches
from numpy.random import randint

from acesta.geo.models import Region
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
    cache = caches["db"]
    regions_rating = cache.get(f"regions_rating_{tourism_type}")
    if regions_rating is None:
        regions_rating = RegionRating.objects.filter(
            tourism_type=tourism_type
        ).prefetch_related("home_code")[:limit]
        cache.set(f"regions_rating_{tourism_type}", regions_rating, 60 * 60 * 24 * 7)
    return regions_rating


def get_top_sights(sight_group: str, limit: int = 3):
    """
    Returns top sights by sight_group
    :param sight_group: str
    :param limit: int
    :return: django.db.models.QuerySet
    """
    cache = caches["db"]
    sights_rating = cache.get(f"sights_cnt_{sight_group}")
    if sights_rating is None:
        sights_rating = SightRating.objects.filter(
            sight_group=sight_group, region_code__isnull=True
        ).prefetch_related("sight", "sight__code", "sight__city")[:limit]
        cache.set(f"sights_cnt_{sight_group}", sights_rating, 60 * 60 * 24 * 7)
    return sights_rating


def get_regions_cnt():
    """
    Returns quantity of regions
    :return: int
    """
    cache = caches["db"]
    regions_cnt = cache.get("regions_cnt")
    if regions_cnt is None:
        regions_cnt = Region.pub.all().count()
        cache.set("regions_cnt", regions_cnt, 60 * 60 * 24 * 7)
    return regions_cnt


def get_sights_cnt():
    """
    Returns quantity of sights
    :return: int
    """
    cache = caches["db"]
    sights_cnt = cache.get("sights_cnt")
    if sights_cnt is None:
        sights_cnt = Sight.pub.all().count()
        cache.set("sights_cnt", sights_cnt, 60 * 60 * 24 * 7)
    return sights_cnt
