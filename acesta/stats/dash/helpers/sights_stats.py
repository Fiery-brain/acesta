from django.conf import settings
from django.db import models

from acesta.geo.models import Sight


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


def get_sight_stats(request) -> list:
    """
    Returns region sight statistics as a list
    :param request: django.http.HttpRequest
    :return: list
    """
    sight_stats = (
        Sight.pub.filter(
            code=request.user.current_region,
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
