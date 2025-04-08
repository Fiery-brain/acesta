from django.db import models

from acesta.base.decorators import to_cache
from acesta.geo.models import Sight
from acesta.geo.models import SightGroup
from acesta.stats.models import CityRating
from acesta.stats.models import RegionRating
from acesta.stats.models import SightRating


@to_cache("amount_rating_place_{code}", 60 * 60 * 24 * 7)
def get_amount_rating_place(**kwargs) -> int:
    """
    Returns rating place by sights amount
    :param: kwargs dict
    :return: int
    """
    sight_rating = (
        Sight.pub.all().values("code").annotate(qty=models.Count("id")).order_by("-qty")
    )
    place = 1
    for place, region in enumerate(sight_rating):
        if region["code"] == kwargs.get("code"):
            place += 1
            break
    return place


@to_cache("interest_rating_place_{code}", 60 * 60 * 24 * 7)
def get_interest_rating_place(**kwargs) -> int:
    """
    Returns rating place by interest
    :param: kwargs dict
    :return: int
    """
    try:
        place = RegionRating.objects.get(
            home_code=kwargs.get("code"),
            tourism_type__isnull=True,
            region_code__isnull=True,
        ).place
    except RegionRating.DoesNotExist:
        place = None
    return place


@to_cache("outstanding_places_{code}", 60 * 60 * 24 * 7)
def get_amount_rating_by_group_outstanding_places(**kwargs) -> list:
    """
    Returns outstanding place
    :param: kwargs dict
    :return: list
    """
    sight_groups = dict(SightGroup.pub.all().values_list("name", "title_gen"))
    sight_rating = (
        Sight.pub.all()
        .values("code", "group__name")
        .annotate(qty=models.Count("id"))
        .order_by("-qty")
    )
    sight_rating_by_group = {}
    for region in sight_rating:
        sight_rating_by_group.setdefault(region["group__name"], []).append(
            {"code": region["code"], "qty": region["qty"]}
        )

    outstanding_places = []
    for group, regions in sight_rating_by_group.items():
        for place, region in enumerate(regions[:3]):
            if region["code"] == kwargs.get("code") and region["qty"] > 1:
                outstanding_places.append(
                    {
                        "group": group,
                        "group_title_gen": sight_groups.get(group),
                        "place": place + 1,
                    }
                )
                break
    outstanding_places = sorted(
        outstanding_places, key=lambda x: (x["place"], x["group_title_gen"])
    )
    return outstanding_places


@to_cache("rating_sight_{code}_{sight_group}", 60 * 60 * 24 * 7)
def get_interest_sight_rating(group_filter, **kwargs):
    return SightRating.objects.filter(
        region_code=kwargs.get("code"), **group_filter
    ).prefetch_related("sight", "sight__group", "sight__code", "sight__city")


def get_tourism_type_filter(tourism_type, from_group=False):
    if not from_group:
        return (
            dict(tourism_type=tourism_type)
            if tourism_type
            else dict(tourism_type__isnull=True)
        )
    else:
        return dict(group__tourism_type=tourism_type) if tourism_type else {}


def get_sight_group_filter(sight_group, include_isnull=True):
    if include_isnull:
        return (
            dict(sight_group=sight_group)
            if sight_group is not None
            else dict(sight_group__isnull=True)
        )
    else:
        return dict(group=sight_group) if sight_group is not None else {}


@to_cache("rating_region_{tourism_type}", 60 * 60 * 24 * 7)
def get_interest_region_rating(tourism_type_filter, **kwargs):
    return RegionRating.objects.filter(
        region_code__isnull=True,
        **tourism_type_filter,
    ).select_related()


@to_cache("rating_cities_{code}_{tourism_type}", 60 * 60 * 24 * 7)
def get_interest_cities_rating(tourism_type_filter, **kwargs):
    return CityRating.objects.filter(
        home_region__code=kwargs.get("code"),
        **tourism_type_filter,
        # **dict(tourism_type=tourism_type) if tourism_type is not None else dict(tourism_type__isnull=True),
    ).select_related()


def get_amount_cities_rating(code, tourism_type_filter):
    return (
        Sight.pub.filter(
            city__isnull=False,
            code=code,
            **tourism_type_filter,
        )
        .values("city", "city__title")
        .annotate(qty=models.Count("id"))
        .order_by("-qty")
    )


def get_amount_region_rating(tourism_type_filter):
    print(tourism_type_filter)
    return (
        Sight.pub.filter(**tourism_type_filter)
        .values("code", "code__title")
        .annotate(qty=models.Count("id"))
        .order_by("-qty")
    )


def get_top_sights(group_filter):
    return SightRating.objects.filter(
        region_code__isnull=True, **group_filter
    ).prefetch_related("sight", "sight__group", "sight__code", "sight__city")[:10]


def get_outside_rating_sight(code, sight_group_filter):
    return Sight.pub.filter(code=code, sight_ratings__isnull=True, **sight_group_filter)
