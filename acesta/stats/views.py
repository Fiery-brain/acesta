import numpy as np
from django.conf import settings
from django.db import models
from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render

from acesta.geo.models import Region
from acesta.geo.models import Sight
from acesta.geo.models import SightGroup
from acesta.stats.dash.helpers.sights_stats import get_sight_stats
from acesta.stats.helpers import get_rating_update_date
from acesta.stats.helpers import get_sights_update_date
from acesta.stats.models import CityRating
from acesta.stats.models import RegionRating
from acesta.stats.models import SightRating
from acesta.user.utils import get_support_form


def region_view(request) -> HttpResponse:
    """
    Region Page representation
    :param request: django.http.HttpRequest
    :return: django.http.HttpResponse
    """

    def get_strong_types(stats: list) -> list:
        """
        Returns a list of strong tourism types in home region
        :param stats: list
        :return: list
        """
        q75 = np.quantile([s["cnt"] for s in stats], 0.75) if len(stats) else 0
        return [
            stat.get("title").replace("туризм", "").lower().strip("- ")
            for stat in stats
            if stat.get("cnt") >= q75 and stat.get("title") is not None
        ]

    def get_weak_types(stats: list) -> list:
        """
        Returns a list of weak tourism types in home region
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

    def get_amount_rating_place() -> int:
        """
        Returns rating place
        :return: int
        """
        sight_rating = (
            Sight.pub.all()
            .values("code")
            .annotate(qty=models.Count("id"))
            .order_by("-qty")
        )
        for place, region in enumerate(sight_rating):
            if region["code"] == request.user.current_region.code:
                return place + 1

    def get_interest_rating_place() -> int:
        """
        Returns rating place
        :return: int
        """
        place = None
        try:
            place = RegionRating.objects.get(
                home_code=request.user.current_region,
                tourism_type__isnull=True,
                region_code__isnull=True,
            ).place
        except RegionRating.DoesNotExist:
            pass
        return place

    def get_amount_rating_by_group_outstanding_places() -> list:
        """
        Returns outstanding place
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
                {
                    "code": region["code"],
                    "qty": region["qty"],
                }
            )

        outstanding_places = []
        for group, regions in sight_rating_by_group.items():
            for place, region in enumerate(regions[:3]):
                if (
                    region["code"] == request.user.current_region.code
                    and region["qty"] > 1
                ):
                    outstanding_places.append(
                        {
                            "group": group,
                            "group_title_gen": sight_groups.get(group),
                            "place": place + 1,
                        }
                    )
                    break
        return sorted(
            outstanding_places, key=lambda x: (x["place"], x["group_title_gen"])
        )

    sight_stats = get_sight_stats(request)

    context = {
        "strong_types": get_strong_types(sight_stats),
        "weak_types": get_weak_types(sight_stats),
        "places_amount": len(Region.pub.all()),
        "amount_rating_place": get_amount_rating_place(),
        "interest_rating_place": get_interest_rating_place(),
        "outstanding_places": get_amount_rating_by_group_outstanding_places(),
        "sights_update_date": get_sights_update_date(),
    }

    if request.GET.get("group", None) is not None:
        context.update(
            {
                "support_form": get_support_form(request.user, settings.SUPPORT_SIGHTS),
                "region_sights": Sight.pub.filter(
                    code=request.user.current_region,
                    **dict(group=request.GET.get("group"))
                    if request.GET.get("group")
                    else {}
                ).prefetch_related("group", "code", "city"),
                "sight_groups": SightGroup.pub.filter(
                    name__in=[
                        group.get("group")
                        for group in Sight.pub.filter(code=request.user.current_region)
                        .values("group")
                        .distinct()
                    ]
                ),
            }
        )
    return render(request, "dashboard/region.html", context)


def rating_view(request, area=settings.AREA_REGIONS) -> HttpResponse:
    """
    Ratings view
    :param request: django.http.HttpRequest
    :param area: str
    :return: django.http.HttpResponse
    """
    context = {"area": area, "rating_update_date": get_rating_update_date()}
    if area != settings.AREA_REGIONS and not request.user.is_extended:
        return redirect("rating")
    else:
        if area == settings.AREA_SIGHTS:
            sight_group = request.user.get_current_sight_group(
                request.GET.get("group", None) or None
            )
            group_filter = (
                dict(sight_group=sight_group)
                if sight_group is not None
                else dict(sight_group__isnull=True)
            )
            sight_group_filter = (
                dict(group=sight_group) if sight_group is not None else {}
            )
            data = {
                "sight_group": sight_group,
                "sight_groups": SightGroup.pub.filter(
                    name__in=[
                        group.get("group")
                        for group in Sight.pub.filter(code=request.user.current_region)
                        .values("group")
                        .distinct()
                    ]
                ),
                "interest_sight_places": SightRating.objects.filter(
                    region_code=request.user.current_region, **group_filter
                ).prefetch_related(
                    "sight", "sight__group", "sight__code", "sight__city"
                ),
                "outside_rating_sight": Sight.pub.filter(
                    code=request.user.current_region,
                    sight_ratings__isnull=True,
                    **sight_group_filter
                ),
                "top_sights": SightRating.objects.filter(
                    region_code__isnull=True, **group_filter
                ).prefetch_related(
                    "sight", "sight__group", "sight__code", "sight__city"
                )[
                    :10
                ],
            }
        elif area == settings.AREA_CITIES:
            if (
                request.user.current_region.region_type
                == settings.REGION_TYPE_FEDERAL_CITY
            ):
                return redirect("rating")
            tourism_type = request.user.get_current_tourism_type(
                request.GET.get("tourism_type", None) or None
            )
            data = {
                "tourism_type": tourism_type,
                "tourism_types": settings.TOURISM_TYPES_OUTSIDE,
                "interest_city_places": CityRating.objects.filter(
                    home_region=request.user.current_region,
                    **dict(tourism_type=tourism_type)
                    if tourism_type is not None
                    else dict(tourism_type__isnull=True)
                ).select_related(),
                "amount_city_places": (
                    Sight.pub.filter(
                        city__isnull=False,
                        code=request.user.current_region,
                        **dict(group__tourism_type=tourism_type)
                        if tourism_type is not None
                        else {}
                    )
                    .values("city", "city__title")
                    .annotate(qty=models.Count("id"))
                    .order_by("-qty")
                ),
            }
        else:
            data = {
                "tourism_types": settings.TOURISM_TYPES_OUTSIDE,
                "interest_region_places": RegionRating.objects.filter(
                    region_code__isnull=True,
                    **(
                        dict(tourism_type=request.GET.get("tourism_type"))
                        if request.GET.get("tourism_type")
                        else dict(tourism_type__isnull=True)
                    )
                ).select_related(),
                "amount_region_places": (
                    Sight.pub.filter(
                        **(
                            dict(group__tourism_type=request.GET.get("tourism_type"))
                            if request.GET.get("tourism_type")
                            else {}
                        )
                    )
                    .values("code", "code__title")
                    .annotate(qty=models.Count("id"))
                    .order_by("-qty")
                ),
            }
    context.update(data)
    return render(request, "dashboard/rating.html", context)


def set_regions_view(request: HttpRequest, code: str) -> HttpResponse:
    """
    Check if received code in paid user regions list
    and sets new home region
    :param request: django.http.HttpRequest
    :param code: str
    :return: django.http.HttpResponse
    """
    region = Region.objects.get(code=code)
    if (
        code in [region.code for region in request.user.regions.all()]
        or region.rank == 0
        or code == request.user.region.code
    ):
        request.user.current_region = region
        request.user.save()
    return redirect("region")
