from django import template

register = template.Library()


@register.filter
def get_prop(obj, key):
    if isinstance(obj, dict):
        return obj.get(key) or obj.get(key.lower())
    elif obj and isinstance(obj, object):
        return getattr(obj, key) or getattr(obj, key.lower())
    else:
        return obj
