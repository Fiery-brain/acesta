from datetime import datetime

from django.conf import settings


def get_date(date_str: str) -> datetime:
    """
    Returns datetime
    :param date_str: str
    :return: datetime
    """
    return datetime.strptime(date_str, settings.PERIOD_DATE_FORMAT)


def format_date(date: datetime) -> str:
    """
    Formats datetime
    :param date: datetime
    :return: str
    """
    return datetime.strftime(date, settings.PERIOD_DATE_FORMAT)
