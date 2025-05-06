from datetime import date
from datetime import datetime

from django.conf import settings
from django.db.models import F

from acesta.base.decorators import to_cache
from acesta.geo.models import Sight
from acesta.stats.models import AudienceRegions
from acesta.stats.models import Indicator
from acesta.stats.models import RegionRating

DEFAULT_SIGHTS_UPDATE_DATE = datetime.fromisoformat("2023-01-01")
DEFAULT_AUDITORY_UPDATE_DATE = datetime.fromisoformat("2023-01-01")
DEFAULT_RATING_UPDATE_DATE = datetime.fromisoformat("2023-01-01")
DEFAULT_AVG_SALARY_UPDATE_DATE = datetime.fromisoformat("2023-01-01")
DEFAULT_AVG_BILL_UPDATE_DATE = datetime.fromisoformat("2023-01-01")


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


@to_cache("indicator_update_date_{value_type}", 60 * 60 * 24 * 7)
def get_last_update_indicator_date(value_type=settings.AVERAGE_SALARY):
    """
    Returns year and month of last update according to indicator
    :param value_type: str
    :return: dict
    """
    try:
        year_month = (
            Indicator.objects.filter(value_type=value_type)
            .annotate(year_month=F("year") * 100 + F("month"))
            .order_by("-year_month")
            .values("year", "month")
            .first()
        ) or {}
    except BaseException:
        year_month = {}
    return year_month.get("year", DEFAULT_AVG_SALARY_UPDATE_DATE.year), year_month.get(
        "month", DEFAULT_AVG_SALARY_UPDATE_DATE.month
    )


@to_cache("avg_salary_update_date", 60 * 60 * 24 * 7)
def get_avg_salary_update_date():
    """
    Returns update date of average salary
    :return: Date
    """
    year, month = get_last_update_indicator_date(value_type=settings.AVERAGE_SALARY)
    return date(year, month, 15)


@to_cache("avg_bill_update_date", 60 * 60 * 24 * 7)
def get_avg_bill_update_date():
    """
    Returns update date of average bills
    :return: Date
    """
    year, month = get_last_update_indicator_date(value_type=settings.AVERAGE_BILL)
    return date(year, month, 15)
