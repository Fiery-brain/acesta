from functools import wraps

from django.core.cache import caches


def to_cache(cache_key_template: str, timeout: int = None, cache_alias: str = "db"):
    """
    Decorator for caching with lazy-loading backend cache
    :param cache_key_template: str
    :param timeout: int
    :param cache_alias: str
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not hasattr(wrapper, "_cache"):
                wrapper._cache = caches[cache_alias]

            try:
                cache_key = cache_key_template.format(*args, **kwargs)
            except (IndexError, KeyError):
                cache_key = cache_key_template

            if not kwargs.get("force_refresh"):
                cached = wrapper._cache.get(cache_key)
                if cached is not None:
                    return cached

            result = func(*args, **kwargs)

            wrapper._cache.set(cache_key, result, timeout)

            return result

        return wrapper

    return decorator


def append(additive_string):
    """
    A decorator that appends an `additive_string` to the result of a function
    :param additive_string: str
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return f"{result}{additive_string}"

        return wrapper

    return decorator
