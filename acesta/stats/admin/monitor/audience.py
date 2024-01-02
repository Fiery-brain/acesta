import datetime

import environ
from django.db import models
from django.utils import timezone

from acesta.geo.models import Region
from acesta.stats.admin.monitor.common import sort_monitor
from acesta.stats.models import AudienceCities
from acesta.stats.models import AudienceRegions

env = environ.Env()


def get_audience_monitor(kwargs) -> dict:
    """
    Returns Audience monitor
    :param kwargs: dict
    :return: dict
    """
    regions_data = {
        r["code"]: {
            "code": r["code"],
            "title": r["code__title"],
            "bad_coeff": 1 if r["mn"] != r["mx"] else 0,
            "coeff": r["mx"],
        }
        for r in AudienceRegions.objects.all()
        .annotate(mn=models.Min("coeff"), mx=models.Max("coeff"))
        .order_by("code")
        .values("code", "code__title", "mn", "mx")
        .distinct()
    }

    no_data_region = {
        code: {"no_data_region": 0 if value else 1}
        for code, value in dict(
            Region.objects.values("code")
            .annotate(qty=models.Count("region_cities__city_audience"))
            .values_list("code", "qty")
        ).items()
    }
    {
        k: v.update(no_data_region.get(k) or {"no_data_region": 0})
        for k, v in regions_data.items()
    }

    no_data_city = {
        code: {"no_data_city": value}
        for code, value in dict(
            Region.objects.values("code")
            .annotate(qty=models.Count("region_cities"))
            .exclude(region_cities__city_audience__isnull=False)
            .values_list("code", "qty")
        ).items()
    }
    {
        k: v.update(no_data_city.get(k) or {"no_data_city": 0})
        for k, v in regions_data.items()
    }

    empty_city = {
        code: {"empty_city": value}
        for code, value in dict(
            AudienceCities.objects.filter(v_all=0)
            .values("code__code", "code__code__title")
            .annotate(qty=models.Count("code", distinct=True))
            .values_list("code__code", "qty")
        ).items()
    }
    {
        k: v.update(empty_city.get(k) or {"empty_city": 0})
        for k, v in regions_data.items()
    }

    bad_coeff_city = {
        code: {"bad_coeff_city": value}
        for code, value in dict(
            AudienceCities.objects.values("code")
            .annotate(
                mn=models.Min("coeff"),
                mx=models.Max("coeff"),
                qty=models.Count("code", distinct=True),
            )
            .exclude(mn=models.F("mx"))
            .values_list("code__code", "qty")
        ).items()
    }
    {
        k: v.update(bad_coeff_city.get(k) or {"bad_coeff_city": 0})
        for k, v in regions_data.items()
    }

    old_data_region = {
        code: {"old_data_region": value}
        for code, value in dict(
            AudienceRegions.objects.filter(
                modified__lt=timezone.now()
                - datetime.timedelta(days=env.int("AUDIENCE_PERIOD", default=180)),
            )
            .values_list("code")
            .annotate(old_data=models.Count("code", distinct=True))
            .values_list("code", "old_data")
        ).items()
    }
    {
        k: v.update(old_data_region.get(k) or {"old_data_region": 0})
        for k, v in regions_data.items()
    }

    old_data_cities = {
        code: {"old_data_cities": value}
        for code, value in dict(
            AudienceCities.objects.filter(
                modified__lt=timezone.now()
                - datetime.timedelta(days=env.int("AUDIENCE_PERIOD", default=180)),
            )
            .values_list("code__code")
            .annotate(old_data=models.Count("code", distinct=True))
            .values_list("code__code", "old_data")
        ).items()
    }
    {
        k: v.update(old_data_cities.get(k) or {"old_data_cities": 0})
        for k, v in regions_data.items()
    }

    if kwargs.get("sort") and kwargs.get("sort").startswith("audience"):
        regions_data = sort_monitor(
            regions_data, kwargs.get("sort").replace("audience_", "")
        )

    return regions_data
