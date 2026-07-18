from django.conf import settings as django_settings
from django.http import HttpRequest

from acesta.front.segment_settings import SECTION_DASHBOARD_TASKS
from acesta.front.segment_settings import SEGMENT_CONFIG


def settings(request: HttpRequest) -> dict:
    """
    Adds settings to context
    :param request: django.http.HttpRequest
    :return: dict
    """
    return dict(
        HOST=f"{request.scheme}://{request.META.get('HTTP_HOST')}",
        PUBLIC_DOMAIN=django_settings.PUBLIC_DOMAIN,
        PUBLIC_URL=f"https://{django_settings.PUBLIC_DOMAIN}",
        TITLE=django_settings.TITLE,
        HASH_TAGS=django_settings.HASH_TAGS,
        SEGMENTS=dict(django_settings.SEGMENTS),
        SEGMENTS_GENITIVE=dict(django_settings.SEGMENTS_GENITIVE_SHORT),
        DEFAULT_SEGMENT=django_settings.DEFAULT_SEGMENT,
        SEGMENT_GOVERNMENT=django_settings.SEGMENT_GOVERNMENT,
        SEGMENT_TIC=django_settings.SEGMENT_TIC,
        SEGMENT_TOUR_OPERATOR=django_settings.SEGMENT_TOUR_OPERATOR,
        SEGMENT_TOUR_AGENT=django_settings.SEGMENT_TOUR_AGENT,
        SEGMENT_TOURISM_PRODUCT_OWNER=django_settings.SEGMENT_TOURISM_PRODUCT_OWNER,
        SEGMENT_INVESTORS=django_settings.SEGMENT_INVESTORS,
        SEGMENT_GUIDE=django_settings.SEGMENT_GUIDE,
        SEGMENT_MARKETING_AGENCY=django_settings.SEGMENT_MARKETING_AGENCY,
        SEGMENT_HOSPITALITY=django_settings.SEGMENT_HOSPITALITY,
        SEGMENT_TOURISM_EVENT=django_settings.SEGMENT_TOURISM_EVENT,
        SEGMENT_TRANSPORTATION=django_settings.SEGMENT_TRANSPORTATION,
        PART_REGION=django_settings.PART_REGION,
        PART_INTEREST=django_settings.PART_INTEREST,
        PART_RATING=django_settings.PART_RATING,
        USER_SEGMENT_TASKS=SEGMENT_CONFIG[SECTION_DASHBOARD_TASKS].get(
            request.user.segment, {}
        )
        if request.user.is_authenticated
        else {},
        DEBUG=django_settings.DEBUG,
        REQUEST_CONSULTATION="consultation",
        REQUEST_PRESENTATION="presentation",
    )
