from .base import *  # noqa
from .base import env

if DEBUG:  # noqa
    from .local import *  # noqa

SITE_ID = 1
TESTING = True

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="tn5CoM0Zdl0qOqGP0iAhUOUIWYHFVkKitkLvEFi1Hr9JBZ1n4e8cuvb2GuGuekO8",
)

# https://docs.djangoproject.com/en/dev/ref/settings/#test-runner
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    },
    "db": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "acesta_cache",
        "TIMEOUT": None,
    },
}

HOME_CODE_BLOCKS = (("01", "02"),)
