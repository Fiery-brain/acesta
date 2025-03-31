import datetime

import environ
from django.db import models
from django.utils import timezone
from Levenshtein import ratio

from acesta.geo.models import Region
from acesta.geo.models import Sight
from acesta.stats.admin.monitor.common import sort_monitor

env = environ.Env()


def get_sights():
    return [
        (
            sight.get("code"),
            sight.get("qt"),
            sum([v for k, v in sight.get("kernel")[:3]]),
            sight.get("code__title"),
            sight.get("id"),
            sight.get("title"),
            sight.get("query"),
            sight.get("query_additional"),
            sight.get("kernel"),
            ratio(sight.get("query"), sight.get("kernel")[0][0])
            if len(sight.get("kernel"))
            else 1,
            ratio(sight.get("query_additional"), sight.get("kernel")[0][0])
            if len(sight.get("kernel"))
            else 1,
            sight.get("similarity_rate"),
            sight.get("is_kernel_checked"),
        )
        for sight in (
            Sight.objects.annotate(qt=models.Sum("sight_all_region_popularity__qty"))
            .filter(is_checked=True, is_pub=True)
            .values(
                "code",
                "qt",
                "kernel",
                "code__title",
                "id",
                "title",
                "query",
                "query_additional",
                "similarity_rate",
                "is_kernel_checked",
            )
        ).order_by("similarity_rate", "code")
    ]


def get_sights_monitor(kwargs) -> dict:
    """
    Returns Sights monitor
    :param kwargs: dict
    :return: dict
    """
    regions_data = {
        r["code"]: {"code": r["code"], "title": r["title"], "qty": r["qty"]}
        for r in Region.objects.all()
        .annotate(qty=models.Count("region_sights"))
        .order_by("code")
        .values("code", "title", "qty")
    }

    not_checked = {
        code: {"not_checked": value}
        for code, value in dict(
            Region.objects.filter(region_sights__is_checked=False)
            .annotate(not_checked=models.Count("region_sights"))
            .values_list("code", "not_checked")
        ).items()
    }
    {
        k: v.update(not_checked.get(k) or {"not_checked": 0})
        for k, v in regions_data.items()
    }

    empty_kernels = {
        code: {"empty_kernels": value}
        for code, value in dict(
            Region.objects.filter(region_sights__kernel=[], region_sights__is_pub=True)
            .annotate(empty_kernels=models.Count("region_sights"))
            .values_list("code", "empty_kernels")
        ).items()
    }
    {
        k: v.update(empty_kernels.get(k) or {"empty_kernels": 0})
        for k, v in regions_data.items()
    }

    old_kernels = {
        code: {"old_kernels": value}
        for code, value in dict(
            Region.objects.filter(
                region_sights__modified_kernel__lt=timezone.now()
                - datetime.timedelta(days=env.int("KERNEL_PERIOD", default=90)),
                region_sights__is_pub=True,
            )
            .annotate(old_kernels=models.Count("region_sights"))
            .values_list("code", "old_kernels")
        ).items()
    }
    {
        k: v.update(old_kernels.get(k) or {"old_kernels": 0})
        for k, v in regions_data.items()
    }

    not_in_region = {
        code: {"not_in_region": value}
        for code, value in dict(
            Region.objects.filter(
                region_sights__is_in_geo_region=False, region_sights__is_pub=True
            )
            .annotate(not_in_region=models.Count("region_sights"))
            .values_list("code", "not_in_region")
        ).items()
    }
    {
        k: v.update(not_in_region.get(k) or {"not_in_region": 0})
        for k, v in regions_data.items()
    }

    empty_titles = {
        code: {"empty_titles": value}
        for code, value in dict(
            Region.objects.filter(
                region_sights__title__isnull=True, region_sights__is_pub=True
            )
            .annotate(empty_titles=models.Count("region_sights"))
            .values_list("code", "empty_titles")
        ).items()
    }
    {
        k: v.update(empty_titles.get(k) or {"empty_titles": 0})
        for k, v in regions_data.items()
    }

    if kwargs.get("sort") and kwargs.get("sort").startswith("sights"):
        regions_data = sort_monitor(
            regions_data, kwargs.get("sort").replace("sights_", "")
        )
    return regions_data


def get_suspicious_kernels(queries_data, kwargs, threshold=0.5) -> list:
    """
    Returns Suspicious queries monitor
    :param queries_data: list
    :param kwargs: dict
    :param threshold: int
    :return: list
    """
    suspicious_kernels = [
        {
            "code": sight[0],
            "title": sight[3],
            "sight_id": sight[4],
            "query": sight[6],
            "query_additional": sight[7],
            "kernel": sight[8][0],
            "ratio": sight[9],
            "similarity_rate": sight[11],
        }
        for sight in queries_data
        if len(sight[8]) and not sight[12]
    ]

    if kwargs.get("sort") and kwargs.get("sort").startswith("suspicious_kernels"):
        column = kwargs.get("sort").replace("suspicious_kernels_", "")
        suspicious_kernels = sorted(
            suspicious_kernels,
            key=lambda x: x.get(column),
            reverse=True if column == "ratio" else False,
        )

    return suspicious_kernels
