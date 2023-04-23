from django import template

register = template.Library()


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
    )
