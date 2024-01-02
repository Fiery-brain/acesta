import datetime
from itertools import groupby

import environ
from django.db import models
from django.utils import timezone

from acesta.geo.models import Region
from acesta.geo.models import Sight
from acesta.stats.admin.monitor.common import sort_monitor

env = environ.Env()


def get_ppt_monitor(queries_data, kwargs) -> dict:
    """
    Returns Popularity monitor
    :param queries_data: list
    :param kwargs: dict
    :return: dict
    """
    regions_data = {
        r["code"]: {"code": r["code"], "title": r["title"]}
        for r in Region.objects.all().order_by("code").values("code", "title")
    }

    wrong_region = {
        code: {"wrong_region": value}
        for code, value in dict(
            Sight.objects.values("code")
            .annotate(qt=models.Count("id"))
            .filter(
                ~models.Q(sight_all_region_popularity__home_code=models.F("code")),
                is_checked=True,
                is_pub=True,
            )
            .exclude(sight_all_region_popularity__home_code__isnull=True)
            .values_list("code", "qt")
        ).items()
    }
    {
        k: v.update(wrong_region.get(k) or {"wrong_region": 0})
        for k, v in regions_data.items()
    }

    no_data = {
        code: {"no_data": value}
        for code, value in dict(
            Sight.objects.values("code")
            .annotate(qt=models.Count("id"))
            .filter(
                is_checked=True,
                is_pub=True,
                sight_all_region_popularity__home_code__isnull=True,
            )
            .values_list("code", "qt")
        ).items()
    }
    {k: v.update(no_data.get(k) or {"no_data": 0}) for k, v in regions_data.items()}

    old_data = {
        code: {"old_data": value}
        for code, value in dict(
            Sight.objects.values("code")
            .annotate(qt=models.Count("id", distinct=True))
            .filter(
                sight_all_region_popularity__modified__lt=timezone.now()
                - datetime.timedelta(days=env.int("POPULARITY_PERIOD", default=30))
            )
            .values_list("code", "qt")
        ).items()
    }
    {k: v.update(old_data.get(k) or {"old_data": 0}) for k, v in regions_data.items()}

    few_queries = {
        code: {"few_queries": len(list(g))}
        for code, g in groupby(
            filter(lambda x: x[1] and x[2] and x[1] / x[2] < 0.3, queries_data),
            key=lambda x: x[0],
        )
    }
    {
        k: v.update(few_queries.get(k) or {"few_queries": 0})
        for k, v in regions_data.items()
    }

    many_queries = {
        code: {"many_queries": len(list(g))}
        for code, g in groupby(
            filter(lambda x: x[1] and x[2] and x[2] / x[1] < 0.3, queries_data),
            key=lambda x: x[0],
        )
    }
    {
        k: v.update(many_queries.get(k) or {"many_queries": 0})
        for k, v in regions_data.items()
    }

    if kwargs.get("sort") and kwargs.get("sort").startswith("ppt"):
        regions_data = sort_monitor(
            regions_data, kwargs.get("sort").replace("ppt_", "")
        )

    return regions_data


def get_suspicious_queries(queries_data, kwargs) -> list:
    """
    Returns Suspicious queries monitor
    :param queries_data: list
    :param kwargs: dict
    :return: list
    """
    suspicious_queries = [
        {
            "code": sight[0],
            "qty": sight[1],
            "kernel": sight[2],
            "title": sight[3],
            "sight_id": sight[4],
            "sight_title": sight[5],
        }
        for sight in queries_data
        if (
            sight[1]
            and sight[2]
            and (sight[1] / sight[2] < 0.3 or sight[2] / sight[1] < 0.3)
        )
        or (sight[2] and not sight[1])
    ]

    if kwargs.get("sort") and kwargs.get("sort").startswith("suspicious_queries"):
        column = kwargs.get("sort").replace("suspicious_queries_", "")
        suspicious_queries = sorted(
            suspicious_queries,
            key=lambda x: x.get(column),
            reverse=True if column in ("qty", "kernel") else False,
        )

    return suspicious_queries
