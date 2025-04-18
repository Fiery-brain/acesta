import time
from functools import wraps
from typing import Callable
from typing import List

from django.core.cache import caches


def fallback_chain(
    models: List[str] = None,
    providers: List[str] = None,
    max_retries: int = 3,
    base_delay: float = 1.0,
):
    """
     Decorator to enumerate LLM models and providers until a valid answer is obtained

    :param models: list
    :param providers: list
    :param max_retries: int
    :param base_delay: float
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            providers_list = providers or [None]

            for attempt in range(max_retries):
                for model in models or [kwargs.get("model")]:
                    for provider in providers_list:
                        try:
                            modified_kwargs = kwargs.copy()
                            modified_kwargs["model"] = model
                            if provider is not None:
                                modified_kwargs["provider"] = provider

                            if attempt > 0:
                                delay = min(base_delay * (2 ** (attempt - 1)), 60)
                                time.sleep(delay)

                            result = func(*args, **modified_kwargs)

                            if result and result.strip():
                                return result

                        except Exception as e:
                            last_exception = e
                            continue

            if last_exception:
                raise last_exception
            return ""

        return wrapper

    return decorator


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

            if result:
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
