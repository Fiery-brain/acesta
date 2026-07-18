import re

from django.conf import settings


def get_valid_segments() -> set[str]:
    return set(settings.SEGMENT_MARKETS) | {key for key, _ in settings.SEGMENTS}


def get_segment_pattern() -> str:
    segments = get_valid_segments() - {settings.DEFAULT_SEGMENT}
    return "|".join(re.escape(segment) for segment in sorted(segments))


def get_segment_market(segment: str | None) -> str:
    return settings.SEGMENT_MARKETS.get(segment, settings.MARKET_B2B)


def timesince_accusatifier(timesince_str):
    """
    Returns timesince in the accusative case
    :param timesince_str: str
    :return: str
    """
    return timesince_str.replace("неделя", "неделю").replace("минута", "минуту")


def timesince_cutter(timesince_str):
    """
    Returns timesince in cut down format
    :param timesince_str: str
    :return: str
    """
    return timesince_str.split(",")[0]
