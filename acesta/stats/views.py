from django.conf import settings
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET

from acesta.geo.models import Region
from acesta.stats.helpers.audience import get_audience_key_data
from acesta.stats.helpers.rating import ensure_current_region_amount_rating_place
from acesta.stats.helpers.rating import get_amount_cities_rating
from acesta.stats.helpers.rating import get_amount_rating_by_group_outstanding_places
from acesta.stats.helpers.rating import get_amount_rating_place
from acesta.stats.helpers.rating import get_amount_region_rating
from acesta.stats.helpers.rating import get_compact_region_rating_rows
from acesta.stats.helpers.rating import get_interest_cities_rating
from acesta.stats.helpers.rating import get_interest_rating_place
from acesta.stats.helpers.rating import get_interest_region_rating
from acesta.stats.helpers.rating import get_interest_sight_rating
from acesta.stats.helpers.rating import get_outside_rating_sight
from acesta.stats.helpers.rating import get_rating_place_change
from acesta.stats.helpers.rating import get_sight_group_filter
from acesta.stats.helpers.rating import get_synced_region_rating_places
from acesta.stats.helpers.rating import get_top_sights
from acesta.stats.helpers.rating import get_tourism_type_filter
from acesta.stats.helpers.recommendations import get_recommendations
from acesta.stats.helpers.sights import get_sight_group_counts
from acesta.stats.helpers.sights import get_sight_groups
from acesta.stats.helpers.sights import get_sight_stats
from acesta.stats.helpers.sights import get_sights_by_group
from acesta.stats.helpers.sights import get_strong_tourism_types
from acesta.stats.helpers.sights import get_weak_tourism_types
from acesta.stats.helpers.sights import prepare_sights_for_template
from acesta.stats.helpers.update_dates import get_rating_update_date
from acesta.stats.helpers.update_dates import get_sights_update_date
from acesta.stats.history import build_history_payload
from acesta.user.utils import get_support_form


REGION_SIGHTS_INITIAL_LIMIT = 20


@require_GET
def history_view(request: HttpRequest) -> JsonResponse:
    """Return normalized history and forecast for the shared dashboard modal."""
    payload = build_history_payload(
        request.user,
        request.GET.get("domain"),
        request.GET.get("entity_type"),
        request.GET.get("entity_id"),
    )
    return JsonResponse(payload)


def region_view(request) -> HttpResponse:
    """
    Region Page representation
    :param request: django.http.HttpRequest
    :return: django.http.HttpResponse
    """

    sight_stats = get_sight_stats(code=request.user.current_region.code)

    context = {
        "strong_types": get_strong_tourism_types(sight_stats),
        "weak_types": get_weak_tourism_types(sight_stats),
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
        sight_group_counts = get_sight_group_counts(
            code=request.user.current_region.code
        )
        group_filter = (
            dict(group=request.GET.get("group")) if request.GET.get("group") else {}
        )
        region_sights = prepare_sights_for_template(
            list(
                get_sights_by_group(request.user.current_region, group_filter)[
                    : REGION_SIGHTS_INITIAL_LIMIT + 1
                ]
            )
        )
        context.update(
            {
                "support_form": get_support_form(request.user, settings.SUPPORT_SIGHTS),
                "region_sights": region_sights[:REGION_SIGHTS_INITIAL_LIMIT],
                "region_sights_has_more": (
                    len(region_sights) > REGION_SIGHTS_INITIAL_LIMIT
                ),
                "sight_groups": get_sight_groups(request.user.current_region),
                "region_sight_count": sight_group_counts["total"],
                "sight_group_counts": sight_group_counts["groups"],
            }
        )
    return render(request, "dashboard/region.html", context)


@require_GET
def region_sights_remaining_view(request) -> HttpResponse:
    """Return all region sights omitted from the initial dashboard response."""

    group = request.GET.get("group")
    group_filter = {"group": group} if group else {}
    region_sights = prepare_sights_for_template(
        list(
            get_sights_by_group(request.user.current_region, group_filter)[
                REGION_SIGHTS_INITIAL_LIMIT:
            ]
        )
    )
    return render(
        request,
        "include/region_sight_rows.html",
        {"region_sights": region_sights},
    )


@require_GET
def region_sight_change_view(request, sight_id: int) -> JsonResponse:
    """Return the current data for a sight in the user's selected region."""
    sight = get_object_or_404(
        get_sights_by_group(request.user.current_region, {}),
        pk=sight_id,
    )
    prepare_sights_for_template([sight])
    return JsonResponse(
        {
            "sight_id": sight.pk,
            "details_html": render_to_string(
                "include/region_sight_change_details.html",
                {"sight": sight},
                request=request,
            ),
        }
    )


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
            interest_sight_places = list(
                get_interest_sight_rating(
                    get_sight_group_filter(sight_group),
                    code=request.user.current_region.code,
                    sight_group=sight_group or "",
                )
            )
            interest_sight_zero_count = len(
                [place for place in interest_sight_places if place.value == 0]
            )

            data = {
                "sight_group": sight_group,
                "sight_groups": get_sight_groups(),
                "interest_sight_places": interest_sight_places,
                "interest_sight_zero_count": interest_sight_zero_count,
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
            interest_city_places = list(
                get_interest_cities_rating(
                    get_tourism_type_filter(tourism_type),
                    code=request.user.current_region.code,
                    tourism_type=tourism_type or "",
                )
            )
            interest_city_zero_count = len(
                [place for place in interest_city_places if place.value == 0]
            )

            data = {
                "tourism_type": tourism_type,
                "tourism_types": settings.TOURISM_TYPES_OUTSIDE,
                "interest_city_places": interest_city_places,
                "interest_city_zero_count": interest_city_zero_count,
                "amount_city_places": get_amount_cities_rating(
                    request.user.current_region,
                    get_tourism_type_filter(tourism_type, True),
                    tourism_type=tourism_type or "",
                ),
            }
        else:
            tourism_type = request.GET.get("tourism_type", "")
            interest_region_places = list(
                get_interest_region_rating(
                    get_tourism_type_filter(tourism_type),
                    tourism_type=tourism_type or "",
                )
            )
            amount_region_places = list(
                get_amount_region_rating(
                    get_tourism_type_filter(tourism_type, True),
                    tourism_type=tourism_type or "",
                )
            )
            amount_region_places = ensure_current_region_amount_rating_place(
                amount_region_places,
                request.user.current_region,
            )
            amount_zero_count = len(
                [place for place in amount_region_places if place["qty"] == 0]
            )
            interest_zero_count = len(
                [place for place in interest_region_places if place.value == 0]
            )
            amount_place = next(
                (
                    place["place"]
                    for place in amount_region_places
                    if place["code"] == request.user.current_region.code
                ),
                None,
            )
            interest_place = next(
                (
                    place.place
                    for place in interest_region_places
                    if place.home_code.code == request.user.current_region.code
                ),
                None,
            )
            amount_compact_places = get_synced_region_rating_places(
                len(amount_region_places),
                amount_place,
                interest_place,
            )
            interest_compact_places = get_synced_region_rating_places(
                len(interest_region_places),
                amount_place,
                interest_place,
            )
            data = {
                "tourism_types": settings.TOURISM_TYPES_OUTSIDE,
                "amount_zero_count": amount_zero_count,
                "interest_zero_count": interest_zero_count,
                "interest_region_places": get_compact_region_rating_rows(
                    interest_region_places,
                    request.user.current_region.code,
                    lambda place: place.home_code.code,
                    get_change=get_rating_place_change,
                    compact_places=interest_compact_places,
                ),
                "amount_region_places": get_compact_region_rating_rows(
                    amount_region_places,
                    request.user.current_region.code,
                    lambda place: place["code"],
                    get_change=lambda place: place.get("change"),
                    compact_places=amount_compact_places,
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
    return redirect(request.META.get("HTTP_REFERER", "region"))


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
