import numpy as np
from django.conf import settings
from django.db import models

from acesta.base.decorators import to_cache
from acesta.geo.models import Sight
from acesta.geo.models import SightGroup


class GroupConcat(models.Aggregate):
    """
    Aggregate function for JOIN related records
    """

    function = "GROUP_CONCAT"
    template = "%(function)s(%(expressions)s)"

    def __init__(self, expression, delimiter, **extra):
        output_field = extra.pop("output_field", models.CharField())
        delimiter = models.Value(delimiter)
        super(GroupConcat, self).__init__(
            expression, delimiter, output_field=output_field, **extra
        )

    def as_postgresql(self, compiler, connection):
        self.function = "STRING_AGG"
        return super(GroupConcat, self).as_sql(compiler, connection)


@to_cache("sight_group_counts_v1_{code}", 60 * 60 * 24 * 30)
def get_sight_group_counts(**kwargs) -> dict:
    """Return cached sight counts for a region and its published groups."""

    code = kwargs.get("code")
    group_counts = (
        Sight.pub.filter(code=code, group__is_pub=True)
        .values("group__name")
        .annotate(count=models.Count("id", distinct=True))
    )
    return {
        "total": Sight.pub.filter(code=code).count(),
        "groups": {
            group_count["group__name"]: group_count["count"]
            for group_count in group_counts
        },
    }


@to_cache("sight_stats_{code}", 60 * 60 * 24 * 7)
def get_sight_stats(**kwargs) -> list:
    """
    Returns region sight statistics as a list
    :param: kwargs dict
    :return: list
    """
    sight_stats = (
        Sight.pub.filter(
            code=kwargs.get("code"),
        )
        .values("group__tourism_type")
        .annotate(cnt=models.Count("id"), groups=GroupConcat("group__title", "|"))
        .order_by("-cnt")
    )
    sight_stats = [
        {
            "name": stat["group__tourism_type"],
            "title": dict(settings.TOURISM_TYPES_OUTSIDE).get(
                stat["group__tourism_type"]
            ),
            "groups": "<br>".join(sorted(list(set(stat["groups"].split("|"))))),
            "cnt": stat["cnt"],
        }
        for stat in sight_stats
    ]
    return list(sight_stats)


def get_strong_tourism_types(stats: list) -> list:
    """
    Returns a list of strong tourism types in a region.
    :param stats: list
    :return: list
    """
    q75 = np.quantile([s["cnt"] for s in stats], 0.75) if len(stats) else 0
    return [
        stat.get("title").replace("туризм", "").lower().strip("- ")
        for stat in stats
        if stat.get("cnt") >= q75 and stat.get("title") is not None
    ]


def get_weak_tourism_types(stats: list) -> list:
    """
    Returns a list of weak tourism types in a region.
    :param stats: list
    :return: list
    """
    weak_names = set(list(dict(settings.TOURISM_TYPES_OUTSIDE).keys())) - set(
        [stat["name"] for stat in stats]
    )
    return [
        title.replace("туризм", "").lower().strip("- ")
        for name, title in settings.TOURISM_TYPES_OUTSIDE
        if name in weak_names
    ]


def get_sight_groups(code=None) -> models.QuerySet:
    """
    Returns groups of sights according to region code
    :param code: str or None
    :return: django.db.models.QuerySet
    """
    if code is not None:
        sight_groups = SightGroup.pub.filter(
            name__in=[
                group.get("group")
                for group in Sight.pub.filter(code=code).values("group").distinct()
            ]
        )
    else:
        sight_groups = SightGroup.pub.all()
    return sight_groups


def get_sights_by_group(code, group_filter):
    return (
        Sight.pub.filter(
            code=code,
            **group_filter,
        )
        .select_related("code", "city")
        .prefetch_related("group")
        .order_by("title", "id")
    )
