import math
from datetime import date

from dateutil.relativedelta import relativedelta
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.template.loader import render_to_string

from acesta.geo.models import Region
from acesta.stats.models import AllCityPopularity
from acesta.stats.models import AllRegionPopularity
from acesta.stats.models import CityCityPopularity
from acesta.stats.models import CityRating
from acesta.stats.models import CityRegionPopularity
from acesta.stats.models import RegionCityPopularity
from acesta.stats.models import RegionRating
from acesta.stats.models import RegionRegionPopularity
from acesta.stats.models import SightRating


HISTORY_MONTHS = 24
FORECAST_MONTHS = 2

POPULARITY_MODELS = {
    "region_region": RegionRegionPopularity,
    "region_city": RegionCityPopularity,
    "city_region": CityRegionPopularity,
    "city_city": CityCityPopularity,
    "sight_region": AllRegionPopularity,
    "sight_city": AllCityPopularity,
}
RATING_MODELS = {
    "region": RegionRating,
    "city": CityRating,
    "sight": SightRating,
}
HISTORY_HEADER_TEMPLATES = {
    "popularity": "include/history_headers/popularity.html",
    "rating_place": "include/history_headers/rating_place.html",
}


def _month(value):
    normalized = getattr(value, "date", lambda: value)()
    return normalized.replace(day=1) if isinstance(normalized, date) else None


def _month_index(value):
    return value.year * 12 + value.month


def _round_value(value, integer):
    value = max(0, value)
    return int(round(value)) if integer else round(value, 2)


def _bounded(value, minimum=0, maximum=None):
    value = max(minimum, value)
    return min(maximum, value) if maximum is not None else value


def _is_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _monthly_values(instance, key, current_key):
    values = {}
    for item in instance.history or []:
        item_month = _month(instance._normalize_history_date(item.get("date")))
        value = item.get(key)
        if item_month is None or not isinstance(value, (int, float)):
            continue
        current = values.get(item_month)
        item_date = instance._normalize_history_date(item.get("date"))
        if current is None or item_date > current[0]:
            values[item_month] = (item_date, float(value))

    current_month = _month(getattr(instance, "modified", None))
    current_value = getattr(instance, current_key, None)
    if current_month and isinstance(current_value, (int, float)):
        values[current_month] = (current_month, float(current_value))
    return {month: value for month, (_, value) in values.items()}


def _normalized_place_values(instance, maximum=None):
    """Return active monthly places with internal inactive runs interpolated."""
    monthly = {}
    for item in instance.history or []:
        item_date = instance._normalize_history_date(item.get("date"))
        item_month = _month(item_date)
        if item_month is None:
            continue
        current = monthly.get(item_month)
        if current is None or item_date > current[0]:
            monthly[item_month] = (item_date, item.get("place"), item.get("value"))

    current_date = getattr(instance, "modified", None)
    current_month = _month(current_date)
    if current_month:
        monthly[current_month] = (
            current_date,
            getattr(instance, "place", None),
            getattr(instance, "value", None),
        )

    ordered_months = sorted(monthly)
    valid_months = [
        month
        for month in ordered_months
        if _is_number(monthly[month][1])
        and monthly[month][1] > 0
        and (maximum is None or monthly[month][1] <= maximum)
        and _is_number(monthly[month][2])
        and monthly[month][2] > 0
    ]
    if not valid_months:
        return {}, set(), set(), None

    values = {month: float(monthly[month][1]) for month in valid_months}
    interpolated = set()
    first_valid = valid_months[0]
    last_valid = valid_months[-1]

    month = first_valid
    while month <= last_valid:
        if month in values:
            month += relativedelta(months=1)
            continue
        previous_month = max(
            candidate for candidate in valid_months if candidate < month
        )
        next_month = min(candidate for candidate in valid_months if candidate > month)
        span = _month_index(next_month) - _month_index(previous_month)
        distance = _month_index(month) - _month_index(previous_month)
        ratio = distance / span
        values[month] = int(
            round(
                values[previous_month]
                + (values[next_month] - values[previous_month]) * ratio
            )
        )
        interpolated.add(month)
        month += relativedelta(months=1)

    blocked = set()
    cursor = ordered_months[0]
    while cursor < first_valid:
        blocked.add(cursor)
        cursor += relativedelta(months=1)
    cursor = last_valid + relativedelta(months=1)
    while cursor <= ordered_months[-1]:
        blocked.add(cursor)
        cursor += relativedelta(months=1)

    return values, interpolated, blocked, last_valid


def _impute(values, start, end, integer, blocked=None, minimum=0, maximum=None):
    blocked = blocked or set()
    normalized = {}
    cursor = start
    while cursor <= end:
        if cursor in blocked:
            cursor += relativedelta(months=1)
            continue
        if cursor in values:
            normalized[cursor] = {
                "value": _round_value(
                    _bounded(values[cursor], minimum, maximum), integer
                ),
                "is_imputed": False,
            }
        else:
            previous = [month for month in values if month < cursor]
            following = [month for month in values if month > cursor]
            if previous and following:
                previous_month = max(previous)
                next_month = min(following)
                span = _month_index(next_month) - _month_index(previous_month)
                distance = _month_index(cursor) - _month_index(previous_month)
                ratio = distance / span
                value = (
                    values[previous_month]
                    + (values[next_month] - values[previous_month]) * ratio
                )
                normalized[cursor] = {
                    "value": _round_value(_bounded(value, minimum, maximum), integer),
                    "is_imputed": True,
                }
            else:
                seasonal = [
                    value
                    for month, value in values.items()
                    if month < cursor and month.month == cursor.month
                ]
                if seasonal:
                    value = sum(seasonal) / len(seasonal)
                    normalized[cursor] = {
                        "value": _round_value(
                            _bounded(value, minimum, maximum), integer
                        ),
                        "is_imputed": True,
                    }
        cursor += relativedelta(months=1)
    return normalized


def _weighted_seasonal(values, target):
    candidates = sorted(
        (
            (month, value)
            for month, value in values.items()
            if month < target and month.month == target.month
        ),
        key=lambda item: item[0],
    )
    if not candidates:
        return None
    weights = range(1, len(candidates) + 1)
    return sum(value * weight for (_, value), weight in zip(candidates, weights)) / sum(
        weights
    )


def _trend_projection(values, target):
    recent = sorted(values.items(), key=lambda item: item[0])[-6:]
    if len(recent) < 3:
        return None
    xs = [_month_index(month) for month, _ in recent]
    ys = [value for _, value in recent]
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    denominator = sum((x - x_mean) ** 2 for x in xs)
    slope = (
        sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denominator
        if denominator
        else 0
    )
    return ys[-1] + slope * (_month_index(target) - xs[-1])


def _forecast(values, end, integer, seasonal_limit=True, minimum=0, maximum=None):
    if len(values) < 3 or end is None:
        return []
    result = []
    for offset in range(1, FORECAST_MONTHS + 1):
        target = end + relativedelta(months=offset)
        seasonal = _weighted_seasonal(values, target)
        trend = _trend_projection(values, target)
        if seasonal is None and trend is None:
            continue
        if seasonal is None:
            predicted = trend
        elif trend is None:
            predicted = seasonal
        else:
            predicted = 0.7 * seasonal + 0.3 * trend
            if seasonal_limit:
                predicted = min(max(predicted, seasonal * 0.8), seasonal * 1.2)
        result.append(
            {
                "date": target.isoformat(),
                "value": _round_value(_bounded(predicted, minimum, maximum), integer),
                "is_forecast": True,
            }
        )
    return result


def _series(instance, specs):
    end = _month(getattr(instance, "modified", None)) or date.today().replace(day=1)
    start = end - relativedelta(months=HISTORY_MONTHS - 1)
    result = []
    for spec in specs:
        is_place = spec["id"] == "place"
        minimum = 1 if is_place else 0
        maximum = spec.get("maximum")
        if is_place:
            values, interpolated, blocked, forecast_end = _normalized_place_values(
                instance, maximum
            )
        else:
            values = _monthly_values(instance, spec["history_key"], spec["current_key"])
            interpolated = set()
            blocked = set()
            forecast_end = end
        normalized = _impute(
            values,
            start,
            end,
            spec["integer"],
            blocked,
            minimum,
            maximum,
        )
        for month in interpolated:
            if month in normalized:
                normalized[month]["is_imputed"] = True
        points = [
            {"date": month.isoformat(), **point, "is_forecast": False}
            for month, point in sorted(normalized.items())
        ]
        result.append(
            {
                "id": spec["id"],
                "name": spec["name"],
                "unit": spec["unit"],
                "axis": spec["axis"],
                "integer": spec["integer"],
                "points": points,
                "forecast": _forecast(
                    values,
                    forecast_end,
                    spec["integer"],
                    seasonal_limit=not is_place,
                    minimum=minimum,
                    maximum=maximum,
                ),
            }
        )
    return result


def _check_popularity_access(user, entity_type, instance):
    current_region_id = user.current_region_id
    if entity_type.startswith("region_"):
        allowed = instance.home_code_id == current_region_id
    elif entity_type.startswith("city_"):
        allowed = user.is_extended and instance.home_code.code_id == current_region_id
    else:
        allowed = user.is_extended and instance.sight.code_id == current_region_id
    if not allowed:
        raise PermissionDenied


def _check_rating_access(user, entity_type, instance):
    if entity_type == "region":
        allowed = instance.region_code_id in (None, user.current_region_id)
    elif entity_type == "city":
        allowed = user.is_extended and instance.home_region_id == user.current_region_id
    else:
        allowed = user.is_extended and instance.region_code_id in (
            None,
            user.current_region_id,
        )
    if not allowed:
        raise PermissionDenied


def _first_sight_group(instance):
    sight = getattr(instance, "sight", None)
    if sight is None:
        return None
    return next(iter(sight.group.all()), None)


def _history_header_context(instance, domain, entity_type):
    context = {
        "domain": domain,
        "entity_type": entity_type,
        "tourism_type": getattr(instance, "tourism_type", None),
    }
    if context["tourism_type"]:
        context["tourism_type_title"] = instance.get_tourism_type_display()

    if domain == "popularity":
        target_type, source_type = entity_type.split("_", 1)
        context.update(
            {
                "target_type": target_type,
                "target": (
                    instance.sight if target_type == "sight" else instance.home_code
                ),
                "source_type": source_type,
                "source": instance.code,
            }
        )
    else:
        context.update(
            {
                "target_type": entity_type,
                "target": (
                    instance.sight if entity_type == "sight" else instance.home_code
                ),
            }
        )

    if context["target_type"] == "sight":
        context["sight_group"] = _first_sight_group(instance)
    return context


def _render_history_header(instance, domain, entity_type):
    return render_to_string(
        HISTORY_HEADER_TEMPLATES[domain],
        _history_header_context(instance, domain, entity_type),
    )


def build_history_payload(user, domain, entity_type, entity_id):
    try:
        entity_id = int(entity_id)
    except (TypeError, ValueError):
        raise Http404 from None

    if domain == "popularity" and entity_type in POPULARITY_MODELS:
        model = POPULARITY_MODELS[entity_type]
        relations = ["code", "home_code"]
        if entity_type.startswith("sight_"):
            relations.extend(("sight", "sight_group"))
        queryset = model.objects.select_related(*relations)
        if entity_type.startswith("sight_"):
            queryset = queryset.prefetch_related("sight__group")
        try:
            instance = queryset.get(pk=entity_id)
        except model.DoesNotExist:
            raise Http404 from None
        _check_popularity_access(user, entity_type, instance)
        specs = [
            {
                "id": "qty",
                "name": "Запросы",
                "history_key": "qty",
                "current_key": "qty",
                "unit": "",
                "axis": "y",
                "integer": True,
            },
            {
                "id": "mean",
                "name": "Популярность",
                "history_key": "mean",
                "current_key": "popularity_mean",
                "unit": "%",
                "axis": "y2",
                "integer": False,
            },
        ]
        reverse_axis = False
    elif domain == "rating_place" and entity_type in RATING_MODELS:
        model = RATING_MODELS[entity_type]
        relations = {
            "region": ("region_code", "home_code"),
            "city": ("city_code", "home_code", "home_region"),
            "sight": ("sight", "region_code"),
        }[entity_type]
        queryset = model.objects.select_related(*relations)
        if entity_type == "sight":
            queryset = queryset.prefetch_related("sight__group")
        try:
            instance = queryset.get(pk=entity_id)
        except model.DoesNotExist:
            raise Http404 from None
        _check_rating_access(user, entity_type, instance)
        specs = [
            {
                "id": "place",
                "name": "Место",
                "history_key": "place",
                "current_key": "place",
                "unit": "",
                "axis": "y",
                "integer": True,
                "maximum": Region.pub.count() if entity_type == "region" else None,
            }
        ]
        reverse_axis = True
    else:
        raise Http404

    return {
        "title": "История и тренды",
        "header_html": _render_history_header(instance, domain, entity_type),
        "domain": domain,
        "reverse_axis": reverse_axis,
        "series": _series(instance, specs),
    }
