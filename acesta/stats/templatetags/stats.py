from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()


METRIC_RANK_LABELS = {
    "rank": ("потенциал", "по потенциалу"),
    "sights": ("потенциал", "по потенциалу"),
    "interest": ("интерес", "по интересу"),
}


def _normalize_int(value):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _get_rank_by_place(place, total):
    place = _normalize_int(place)
    total = _normalize_int(total)
    if place is None or total is None or place < 1 or total < 1 or place > total:
        return None
    if total == 1:
        return 4
    return max(0, min(4, 4 - int((place - 1) * 5 / total)))


def _get_metric_rank(metric=None, rank=None, place=None, total=None, group=False):
    if metric not in METRIC_RANK_LABELS:
        return None
    rank = (
        _normalize_int(rank) if rank is not None else _get_rank_by_place(place, total)
    )
    if rank is None:
        return None
    rank = max(0, min(4, rank))
    title = dict(settings.REGION_RANKS).get(rank)
    if title is None:
        return None
    if group and title == "Лидер":
        title = "Лидеры"
    metric_label, leader_metric_label = METRIC_RANK_LABELS[metric]
    metric_text = leader_metric_label if rank == 4 else metric_label
    return {
        "rank": rank,
        "title": title,
        "metric_class": f"metric-{metric}",
        "rank_class": f"rank-{rank}",
        "class_name": f"metric metric-{metric} rank-{rank}",
        "text": f"{title} {metric_text}",
    }


@register.simple_tag
def metric_rank(metric=None, rank=None, place=None, total=None, group=False):
    return _get_metric_rank(
        metric=metric,
        rank=rank,
        place=place,
        total=total,
        group=group,
    )


@register.filter
def get_medal_class(place) -> str:
    """
    Returns a medal classes by place
    :param place: int
    :return: str
    """
    medal_class = "medal "
    if place == 1:
        medal_class += "gold"
    elif place == 2:
        medal_class += "silver"
    elif place == 3:
        medal_class += "bronze"
    return medal_class


@register.inclusion_tag("include/place_block.html")
def place_block(*args, **kwargs):
    metric_rank = _get_metric_rank(
        metric=kwargs.get("metric"),
        rank=kwargs.get("rank"),
        place=kwargs.get("place", kwargs.get("value")),
        total=kwargs.get("total"),
    )
    return dict(
        text_class_base=kwargs.get("text_class_base"),
        border_class_base=kwargs.get("border_class_base"),
        text_class=kwargs.get("text_class", ""),
        border_class=kwargs.get("border_class", ""),
        value=kwargs.get("value", 0),
        value_name=kwargs.get("value_name", "место"),
        desc=kwargs.get("desc"),
        total=kwargs.get("total"),
        tooltip_text=kwargs.get("tooltip_text"),
        is_change=isinstance(kwargs.get("change"), int),
        change=kwargs.get("change"),
        metric_rank=metric_rank,
        place_group=kwargs.get("place_group"),
    )


def _get_place_change(value):
    if isinstance(value, dict):
        return value.get("change")
    if hasattr(value, "change"):
        return value.change
    return value


def _normalize_place_change(change):
    if change in (None, ""):
        return None
    if isinstance(change, str):
        try:
            return int(change)
        except ValueError:
            return None
    return change


@register.inclusion_tag("include/place_change.html")
def place_change(value):
    change = _normalize_place_change(_get_place_change(value))
    if change is None:
        return {
            "change_text": mark_safe("&nbsp;"),
            "change_class": "place_change_neural",
        }
    if change == 0:
        return {
            "change_text": "+0",
            "change_class": "place_change_neural",
        }
    if change < 0:
        return {
            "change_text": change,
            "change_class": "place_change_negative",
        }
    return {
        "change_text": f"+{change}",
        "change_class": "",
    }
