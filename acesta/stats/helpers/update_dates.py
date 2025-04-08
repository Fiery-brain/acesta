from datetime import datetime

from acesta.base.decorators import to_cache
from acesta.geo.models import Sight
from acesta.stats.models import AudienceRegions
from acesta.stats.models import RegionRating

DEFAULT_SIGHTS_UPDATE_DATE = datetime.fromisoformat("2023-01-01")
DEFAULT_AUDITORY_UPDATE_DATE = datetime.fromisoformat("2023-01-01")
DEFAULT_RATING_UPDATE_DATE = datetime.fromisoformat("2023-01-01")


@to_cache("sights_update_date", 60 * 60 * 24 * 7)
def get_sights_update_date():
    """
    Returns last update date of sights
    :return: Datetime
    """
    try:
        sights_update_date = Sight.pub.order_by("-modified").first().modified
    except AttributeError:
        sights_update_date = DEFAULT_SIGHTS_UPDATE_DATE
    return sights_update_date


@to_cache("auditory_update_date", 60 * 60 * 24 * 7)
def get_auditory_update_date():
    """
    Returns last update date of auditory
    :return: Datetime
    """
    try:
        auditory_update_date = (
            AudienceRegions.objects.order_by("-modified").first().modified
        )
    except AttributeError:
        auditory_update_date = DEFAULT_AUDITORY_UPDATE_DATE
    return auditory_update_date


@to_cache("rating_update_date", 60 * 60 * 24 * 7)
def get_rating_update_date():
    """
    Returns update date of rating
    :return: Datetime
    """
    try:
        rating_update_date = RegionRating.objects.first().modified
    except AttributeError:
        rating_update_date = DEFAULT_AUDITORY_UPDATE_DATE
    return rating_update_date
