from dateutil.relativedelta import relativedelta
from django.db import models
from django.db.models import Exists
from django.db.models import OuterRef
from django.db.models import Prefetch
from django.utils import timezone

from acesta.base.decorators import to_cache
from acesta.geo.models import Sight
from acesta.geo.models import SightGroup
from acesta.stats.models import CityRating
from acesta.stats.models import RegionRating
from acesta.stats.models import SightRating


RATING_FIELDS = (
    "id",
    "modified",
    "history",
    "rating_type",
    "place",
    "value",
)
SIGHT_FIELDS = (
    "id",
    "title",
    "rate",
    "code_id",
    "city_id",
)
REGION_FIELDS = (
    "code",
    "title",
    "region_type",
)
CITY_FIELDS = (
    "id",
    "title",
)


def _filter_sights_by_tourism_type(sights, tourism_type):
    if not tourism_type:
        return sights

    sight_groups = Sight.group.through.objects.filter(
        sight_id=OuterRef("pk"),
        sightgroup__tourism_type=tourism_type,
    )
    return sights.filter(Exists(sight_groups))


def _sight_rating_relations(ratings):
    return (
        ratings.select_related("sight", "sight__code", "sight__city")
        .prefetch_related(
            Prefetch(
                "sight__group",
                queryset=SightGroup.objects.only("name", "title"),
            )
        )
        .only(
            *RATING_FIELDS,
            "sight_id",
            *(f"sight__{field}" for field in SIGHT_FIELDS),
            *(f"sight__code__{field}" for field in REGION_FIELDS),
            *(f"sight__city__{field}" for field in CITY_FIELDS),
        )
    )


@to_cache("amount_rating_state_v2", 60 * 60 * 24 * 7)
def get_amount_rating_state(**kwargs) -> dict:
    """
    Returns rating state by sights amount
    :param: kwargs dict
    :return: dict
    """

    def _build_amount_rating_places(sights) -> dict:
        sight_rating = (
            sights.values("code").annotate(qty=models.Count("id")).order_by("-qty")
        )
        return {
            region["code"]: {"place": place, "qty": region["qty"]}
            for place, region in enumerate(sight_rating, start=1)
        }

    rating_state = _build_amount_rating_places(Sight.pub.all())
    previous_rating_state = _build_amount_rating_places(
        Sight.pub.filter(created__lte=timezone.now() - relativedelta(months=1))
    )
    for code, rating in rating_state.items():
        previous_rating = previous_rating_state.get(code, {})
        previous_place = previous_rating.get("place")
        rating.update(
            {
                "previous_place": previous_place,
                "change": (
                    previous_place - rating["place"]
                    if previous_place is not None
                    else None
                ),
                "previous_qty": previous_rating.get("qty"),
            }
        )
    return rating_state


def get_amount_rating_place(**kwargs) -> dict:
    """
    Returns rating place by sights amount
    :param: kwargs dict
    :return: dict
    """
    code = kwargs.get("code")
    rating = get_amount_rating_state(force_refresh=kwargs.get("force_refresh")).get(
        code
    )
    if rating is not None:
        return rating
    return {
        "place": None,
        "previous_place": None,
        "change": None,
        "qty": None,
        "previous_qty": None,
    }


def _build_amount_rating_rows(sights, *fields) -> list:
    sight_rating = (
        sights.values(*fields).annotate(qty=models.Count("id")).order_by("-qty")
    )
    return [
        {**rating, "place": place} for place, rating in enumerate(sight_rating, start=1)
    ]


def _add_previous_amount_rating(rows, previous_rows, key) -> list:
    previous_rating = {rating[key]: rating for rating in previous_rows}
    for rating in rows:
        previous_place = previous_rating.get(rating[key], {}).get("place")
        rating.update(
            {
                "previous_place": previous_place,
                "change": (
                    previous_place - rating["place"]
                    if previous_place is not None
                    else None
                ),
                "previous_qty": previous_rating.get(rating[key], {}).get("qty"),
            }
        )
    return rows


@to_cache("amount_region_rating_state_v3_{tourism_type}", 60 * 60 * 24 * 7)
def get_amount_region_rating_state(**kwargs) -> list:
    tourism_type = kwargs.get("tourism_type") or ""
    previous_date = timezone.now() - relativedelta(months=1)
    rating_rows = _build_amount_rating_rows(
        _filter_sights_by_tourism_type(Sight.pub.all(), tourism_type),
        "code",
        "code__title",
    )
    previous_rating_rows = _build_amount_rating_rows(
        _filter_sights_by_tourism_type(
            Sight.pub.filter(created__lte=previous_date),
            tourism_type,
        ),
        "code",
        "code__title",
    )
    return _add_previous_amount_rating(rating_rows, previous_rating_rows, "code")


@to_cache("amount_city_rating_state_v3_{code}_{tourism_type}", 60 * 60 * 24 * 7)
def get_amount_city_rating_state(**kwargs) -> list:
    tourism_type = kwargs.get("tourism_type") or ""
    code = kwargs.get("code")
    previous_date = timezone.now() - relativedelta(months=1)
    sight_filter = {
        "city__isnull": False,
        "code": code,
    }
    rating_rows = _build_amount_rating_rows(
        _filter_sights_by_tourism_type(
            Sight.pub.filter(**sight_filter),
            tourism_type,
        ),
        "city",
        "city__title",
    )
    previous_rating_rows = _build_amount_rating_rows(
        _filter_sights_by_tourism_type(
            Sight.pub.filter(created__lte=previous_date, **sight_filter),
            tourism_type,
        ),
        "city",
        "city__title",
    )
    return _add_previous_amount_rating(rating_rows, previous_rating_rows, "city")


@to_cache("interest_rating_place_v3_{code}", 60 * 60 * 24 * 7)
def get_interest_rating_place(**kwargs) -> dict:
    """
    Returns rating place by interest
    :param: kwargs dict
    :return: dict
    """

    def _empty_interest_rating_place():
        return {
            "place": None,
            "previous_place": None,
            "change": None,
            "value": None,
            "previous_value": None,
        }

    try:
        rating = RegionRating.objects.get(
            home_code=kwargs.get("code"),
            tourism_type__isnull=True,
            region_code__isnull=True,
        )
    except RegionRating.DoesNotExist:
        return _empty_interest_rating_place()

    previous_place = rating.get_previous_history_value("place")
    return {
        "place": rating.place,
        "previous_place": previous_place,
        "change": rating.change,
        "value": rating.value,
        "previous_value": rating.get_previous_history_value("value"),
    }


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


@to_cache("rating_sight_v3_{code}_{sight_group}", 60 * 60 * 24 * 7)
def get_interest_sight_rating(group_filter, **kwargs):
    return _sight_rating_relations(
        SightRating.objects.filter(region_code=kwargs.get("code"), **group_filter)
    )


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


@to_cache("rating_region_v3_{tourism_type}", 60 * 60 * 24 * 7)
def get_interest_region_rating(tourism_type_filter, **kwargs):
    return (
        RegionRating.objects.filter(
            region_code__isnull=True,
            **tourism_type_filter,
        )
        .select_related("home_code")
        .only(
            *RATING_FIELDS,
            "home_code_id",
            "home_code__code",
            "home_code__title",
        )
    )


def _get_rank_by_place(place, total):
    if place is None or total < 1 or place < 1 or place > total:
        return None
    if total == 1:
        return 4
    return max(0, min(4, 4 - int((place - 1) * 5 / total)))


def _add_region_rating_ranks(rows, total):
    rating_rows = [row for row in rows if row["type"] == "row"]
    for row in rating_rows:
        if row["type"] != "row":
            continue
        row["rank"] = _get_rank_by_place(row["place"], total)
    for index, row in enumerate(rating_rows):
        previous_row = rating_rows[index - 1] if index > 0 else None
        next_row = rating_rows[index + 1] if index + 1 < len(rating_rows) else None
        row["is_rank_start"] = (
            previous_row is None or previous_row["rank"] != row["rank"]
        )
        row["is_rank_end"] = next_row is None or next_row["rank"] != row["rank"]


def get_compact_region_rating_rows(
    rating_places,
    current_region_code,
    get_region_code,
    get_change=None,
    compact_places=None,
    top_count=3,
    bottom_count=3,
):
    """
    Prepares rating rows with compact visibility markers.
    :param rating_places: list
    :param current_region_code: str
    :param get_region_code: callable
    :param get_change: callable
    :param compact_places: set
    :param top_count: int
    :param bottom_count: int
    :return: dict
    """
    rating_places = list(rating_places)
    total = len(rating_places)

    def _get_place(place):
        if isinstance(place, dict):
            return place.get("place")
        return getattr(place, "place")

    if compact_places is None:
        compact_places = get_synced_region_rating_places(total)

    rows = []
    previous_compact_place = None
    for index, place in enumerate(rating_places):
        current_place = _get_place(place)
        is_compact_visible = current_place in compact_places
        if (
            is_compact_visible
            and previous_compact_place is not None
            and current_place - previous_compact_place > 1
        ):
            rows.append({"type": "gap", "place": previous_compact_place + 1})

        rows.append(
            {
                "type": "row",
                "item": place,
                "place": current_place,
                "is_current": get_region_code(place) == current_region_code,
                "is_compact_visible": is_compact_visible,
                "change": get_change(place) if get_change is not None else None,
            }
        )
        if is_compact_visible:
            previous_compact_place = current_place

    _add_region_rating_ranks(rows, total)

    return {
        "rows": rows,
        "total": total,
        "has_extra": any(place not in compact_places for place in range(1, total + 1)),
    }


def get_rating_place_change(rating):
    """
    Returns rating place change from previous history item.
    :param rating: Rating
    :return: int | None
    """
    return rating.change


def ensure_current_region_amount_rating_place(amount_region_places, current_region):
    """
    Adds current region to amount rating when it has no sights in selected filter.
    :param amount_region_places: list
    :param current_region: Region
    :return: list
    """
    amount_region_places = list(amount_region_places)
    if not any(place["code"] == current_region.code for place in amount_region_places):
        amount_region_places.append(
            {
                "code": current_region.code,
                "code__title": current_region.title,
                "qty": 0,
                "place": len(amount_region_places) + 1,
                "previous_place": None,
                "change": None,
                "previous_qty": None,
                "is_virtual": True,
            }
        )
    return amount_region_places


def get_synced_region_rating_places(
    total,
    amount_place=None,
    interest_place=None,
    top_count=3,
    bottom_count=3,
    range_padding=2,
    large_gap_threshold=10,
):
    """
    Returns places visible in both compact region ratings.
    :param total: int
    :param amount_place: int
    :param interest_place: int
    :param top_count: int
    :param bottom_count: int
    :param range_padding: int
    :param large_gap_threshold: int
    :return: set
    """
    compact_places = set(range(1, min(top_count, total) + 1))
    compact_places.update(range(max(total - bottom_count + 1, 1), total + 1))
    if amount_place is not None and interest_place is not None:
        if abs(amount_place - interest_place) > large_gap_threshold:
            for place in (amount_place, interest_place):
                range_start = max(place - range_padding, 1)
                range_end = min(place + range_padding, total)
                compact_places.update(range(range_start, range_end + 1))
        else:
            range_start = max(min(amount_place, interest_place) - range_padding, 1)
            range_end = min(max(amount_place, interest_place) + range_padding, total)
            compact_places.update(range(range_start, range_end + 1))
    return compact_places


@to_cache("rating_cities_v3_{code}_{tourism_type}", 60 * 60 * 24 * 7)
def get_interest_cities_rating(tourism_type_filter, **kwargs):
    return (
        CityRating.objects.filter(
            home_region__code=kwargs.get("code"),
            **tourism_type_filter,
        )
        .select_related("home_code")
        .only(
            *RATING_FIELDS,
            "home_code_id",
            "home_code__id",
            "home_code__title",
        )
    )


def get_amount_cities_rating(code, tourism_type_filter=None, tourism_type=""):
    return get_amount_city_rating_state(
        code=getattr(code, "code", code),
        tourism_type=tourism_type,
    )


def get_amount_region_rating(tourism_type_filter=None, tourism_type=""):
    return get_amount_region_rating_state(tourism_type=tourism_type)


def get_top_sights(group_filter):
    return _sight_rating_relations(
        SightRating.objects.filter(region_code__isnull=True, **group_filter)
    )[:10]


def get_outside_rating_sight(code, sight_group_filter):
    ratings = SightRating.objects.filter(sight_id=OuterRef("pk"))
    return (
        Sight.pub.filter(code=code, **sight_group_filter)
        .filter(~Exists(ratings))
        .select_related("code", "city")
        .prefetch_related(
            Prefetch(
                "group",
                queryset=SightGroup.objects.only("name", "title"),
            )
        )
        .only(
            *SIGHT_FIELDS,
            *(f"code__{field}" for field in REGION_FIELDS),
            *(f"city__{field}" for field in CITY_FIELDS),
        )
    )
