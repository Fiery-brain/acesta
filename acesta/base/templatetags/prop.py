from django import template

register = template.Library()


@register.filter
def get_prop(obj, key):
    """

    :param obj: object
    :param key: str
    :return:
    """
    if isinstance(obj, dict):
        return obj.get(key, "")
    elif isinstance(obj, object):
        return getattr(obj, key, "")
    else:
        return obj
