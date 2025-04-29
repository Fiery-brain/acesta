import numpy as np
from django.conf import settings
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render

from acesta.geo.models import Region
from acesta.stats.helpers.audience import get_audience_key_data
from acesta.stats.helpers.rating import get_amount_cities_rating
from acesta.stats.helpers.rating import get_amount_rating_by_group_outstanding_places
from acesta.stats.helpers.rating import get_amount_rating_place
from acesta.stats.helpers.rating import get_amount_region_rating
from acesta.stats.helpers.rating import get_interest_cities_rating
from acesta.stats.helpers.rating import get_interest_rating_place
from acesta.stats.helpers.rating import get_interest_region_rating
from acesta.stats.helpers.rating import get_interest_sight_rating
from acesta.stats.helpers.rating import get_outside_rating_sight
from acesta.stats.helpers.rating import get_sight_group_filter
from acesta.stats.helpers.rating import get_top_sights
from acesta.stats.helpers.rating import get_tourism_type_filter
from acesta.stats.helpers.recommendations import get_recommendations
from acesta.stats.helpers.sights import get_sight_groups
from acesta.stats.helpers.sights import get_sight_stats
from acesta.stats.helpers.sights import get_sights_by_group
from acesta.stats.helpers.update_dates import get_rating_update_date
from acesta.stats.helpers.update_dates import get_sights_update_date
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

    sight_stats = get_sight_stats(code=request.user.current_region.code)

    context = {
        "strong_types": get_strong_types(sight_stats),
        "weak_types": get_weak_types(sight_stats),
        "places_amount": len(Region.pub.all()),
        "amount_rating_place": get_amount_rating_place(
            code=request.user.current_region.code
        ),
        "interest_rating_place": get_interest_rating_place(
            code=request.user.current_region.code
        ),
        "outstanding_places": get_amount_rating_by_group_outstanding_places(
            code=request.user.current_region.code
        ),
        "sights_update_date": get_sights_update_date(),
    }

    if request.GET.get("group", None) is not None:
        group_filter = (
            dict(group=request.GET.get("group")) if request.GET.get("group") else {}
        )
        context.update(
            {
                "support_form": get_support_form(request.user, settings.SUPPORT_SIGHTS),
                "region_sights": get_sights_by_group(
                    request.user.current_region, group_filter
                ),
                "sight_groups": get_sight_groups(request.user.current_region),
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

            data = {
                "sight_group": sight_group,
                "sight_groups": get_sight_groups(),
                "interest_sight_places": get_interest_sight_rating(
                    get_sight_group_filter(sight_group),
                    code=request.user.current_region.code,
                    sight_group=sight_group or "",
                ),
                "outside_rating_sight": get_outside_rating_sight(
                    request.user.current_region,
                    get_sight_group_filter(sight_group, False),
                ),
                "top_sights": get_top_sights(get_sight_group_filter(sight_group)),
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
                "interest_city_places": get_interest_cities_rating(
                    get_tourism_type_filter(tourism_type),
                    code=request.user.current_region.code,
                    tourism_type=tourism_type or "",
                ),
                "amount_city_places": get_amount_cities_rating(
                    request.user.current_region,
                    get_tourism_type_filter(tourism_type, True),
                ),
            }
        else:
            tourism_type = request.GET.get("tourism_type", "")
            data = {
                "tourism_types": settings.TOURISM_TYPES_OUTSIDE,
                "interest_region_places": get_interest_region_rating(
                    get_tourism_type_filter(tourism_type),
                    tourism_type=tourism_type or "",
                ),
                "amount_region_places": get_amount_region_rating(
                    get_tourism_type_filter(tourism_type, True)
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
    request.user.current_region = region
    request.user.save()
    return redirect("region")


def get_recommendations_view(request: HttpRequest, part: str) -> JsonResponse:
    """
    Returns a JSON object with recommendations by request data
    :param request: django.http.HttpRequest
    :param part: str
    :return: JsonResponse
    """

    def check_data() -> dict:
        """
        Checks whether the user can view the requested data.
        :return: dict
        """
        data = {
            key: item
            for key, item in request.POST.items()
            if key != "csrfmiddlewaretoken"
        }

        if part == settings.PART_INTEREST:
            home_area, home_pk = data.get("data[home_area_key]").split("_")
            audience_pk, tourism_type, area = get_audience_key_data(
                data.get("data[audience_key]")
            )

            if not request.user.is_extended:
                home_area = settings.AREA_REGIONS
                area = settings.AREA_REGIONS

            if home_area != settings.AREA_REGIONS:
                tourism_type = request.user.get_current_tourism_type(tourism_type)

            data = dict(
                home_area=home_area,
                home_pk=home_pk,
                audience_pk=audience_pk,
                tourism_type=tourism_type,
                area=area,
            )
        elif part == settings.PART_RATING:
            group = ""
            area, tourism_type = data.get("data[rating_key]").split("_")
            if area == settings.AREA_SIGHTS:
                group = tourism_type

            if not request.user.is_extended:
                area = settings.AREA_REGIONS

            if area != settings.AREA_REGIONS:
                tourism_type = request.user.get_current_tourism_type(tourism_type)
                group = request.user.get_current_sight_group(group)

            data = dict(area=area, tourism_type=tourism_type, group=group)

        return data

    try:
        recommendations = get_recommendations(
            part,
            request.user.current_region,
            request.user.segment,
            check_data(),
        )
    except KeyError:
        recommendations = ""

    return JsonResponse({"recommendations": recommendations})
