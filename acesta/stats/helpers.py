from django.core.cache import caches

from acesta.geo.models import Sight
from acesta.stats.models import AudienceRegions
from acesta.stats.models import RegionRating


def get_sights_update_date():
    """
    Returns last update date of sights
    :return: Datetime
    """
    cache = caches["db"]
    sights_update_date = cache.get("sights_update_date")
    if sights_update_date is None:
        sights_update_date = Sight.pub.order_by("-modified").first().modified
        cache.set("sights_update_date", sights_update_date, 60 * 60 * 24 * 7)
    return sights_update_date


def get_auditory_update_date():
    """
    Returns last update date of auditory
    :return: Datetime
    """
    cache = caches["db"]
    auditory_update_date = cache.get("auditory_update_date")
    if auditory_update_date is None:
        auditory_update_date = (
            AudienceRegions.objects.order_by("-modified").first().modified
        )
        cache.set("auditory_update_date", auditory_update_date, 60 * 60 * 24 * 7)
    return auditory_update_date


def get_rating_update_date():
    """
    Returns update date of rating
    :return: Datetime
    """
    cache = caches["db"]
    rating_update_date = cache.get("rating_update_date")
    if rating_update_date is None:
        rating_update_date = RegionRating.objects.first().modified
        cache.set("rating_update_date", rating_update_date, 60 * 60 * 24 * 7)
    return rating_update_date
