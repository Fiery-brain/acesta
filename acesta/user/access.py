from django.conf import settings
from django.utils import timezone

from acesta.geo.models import Region
from acesta.user import get_date


def allowed_region_codes(user):
    """Return regions currently available through the owner's access level."""
    codes = set(Region.pub.filter(rank=0).values_list("code", flat=True))
    paid_codes = set(user.regions.values_list("code", flat=True))
    period_info = user.period_info or {}
    now = timezone.now()
    for code in paid_codes:
        period = period_info.get(code)
        if not period or not period.get("end"):
            codes.add(code)
            continue
        try:
            if get_date(period["end"]) >= now:
                codes.add(code)
        except (TypeError, ValueError):
            continue
    return codes


def allowed_tourism_types(user):
    """Return the tourism types allowed by the owner's current access level."""
    configured = dict(settings.TOURISM_TYPES_OUTSIDE)
    return set(user.tourism_types or configured)


def has_region_access(user, code):
    return user.is_active and str(code) in allowed_region_codes(user)


def has_tourism_type_access(user, tourism_type):
    return user.is_active and (
        not tourism_type or tourism_type in allowed_tourism_types(user)
    )
