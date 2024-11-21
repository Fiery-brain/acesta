from datetime import datetime

from django.core.cache import caches

from acesta.geo.models import Sight
from acesta.stats.models import AudienceRegions
from acesta.stats.models import RegionRating

DEFAULT_SIGHTS_UPDATE_DATE = datetime.fromisoformat("2023-01-01")
DEFAULT_AUDITORY_UPDATE_DATE = datetime.fromisoformat("2023-01-01")
DEFAULT_RATING_UPDATE_DATE = datetime.fromisoformat("2023-01-01")


def get_sights_update_date():
    """
    Returns last update date of sights
    :return: Datetime
    """
    cache = caches["db"]
    sights_update_date = cache.get("sights_update_date")
    if sights_update_date is None:
        try:
            sights_update_date = Sight.pub.order_by("-modified").first().modified
            cache.set("sights_update_date", sights_update_date, 60 * 60 * 24 * 7)
        except AttributeError:
            sights_update_date = DEFAULT_SIGHTS_UPDATE_DATE
    return sights_update_date


def get_auditory_update_date():
    """
    Returns last update date of auditory
    :return: Datetime
    """
    cache = caches["db"]
    auditory_update_date = cache.get("auditory_update_date")
    if auditory_update_date is None:
        try:
            auditory_update_date = (
                AudienceRegions.objects.order_by("-modified").first().modified
            )
            cache.set("auditory_update_date", auditory_update_date, 60 * 60 * 24 * 7)
        except AttributeError:
            auditory_update_date = DEFAULT_AUDITORY_UPDATE_DATE
    return auditory_update_date


def get_rating_update_date():
    """
    Returns update date of rating
    :return: Datetime
    """
    cache = caches["db"]
    rating_update_date = cache.get("rating_update_date")
    if rating_update_date is None:
        try:
            rating_update_date = RegionRating.objects.first().modified
            cache.set("rating_update_date", rating_update_date, 60 * 60 * 24 * 7)
        except AttributeError:
            rating_update_date = DEFAULT_AUDITORY_UPDATE_DATE
    return rating_update_date
