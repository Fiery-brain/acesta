"""
Base settings to build other settings files upon.
"""
from email.utils import getaddresses
from pathlib import Path

import environ

ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
APPS_DIR = ROOT_DIR / "acesta"
env = environ.Env()

env.read_env(str(ROOT_DIR / ".env"))

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool("DJANGO_DEBUG", False)
# Local time zone. Choices are
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# though not all of them may be available with every OS.
# In Windows, this must be set to your system time zone.
TIME_ZONE = "Europe/Moscow"
# https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = "ru-RU"
# https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1
# https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True

USE_THOUSAND_SEPARATOR = True

# DATABASES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {"default": env.db("DATABASE_URL", default="sqlite:////:memory:")}

DATABASES["default"]["ATOMIC_REQUESTS"] = True

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# URLS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = "config.urls"
# https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = "config.wsgi.application"

# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "django.forms",
]
THIRD_PARTY_APPS = [
    "db_mutex",
    "django_json_widget",
    "django_plotly_dash.apps.DjangoPlotlyDashConfig",
    "channels",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.vk",
    "allauth.socialaccount.providers.yandex",
    "acesta.socialaccount.providers.leaderid",
    "allauth.socialaccount.providers.google",
]

LOCAL_APPS = [
    "acesta.front",
    "acesta.geo",
    "acesta.stats",
    "acesta.user",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

ASGI_APPLICATION = "acesta.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                ("127.0.0.1", 6379),
            ],
        },
    },
}

# MIGRATIONS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#migration-modules
MIGRATION_MODULES = {"sites": "acesta.contrib.sites.migrations"}

# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

PLOTLY_DASH = {
    # Name of view wrapping function
    "view_decorator": "django_plotly_dash.access.login_required",
}

AUTH_USER_MODEL = "user.User"

LOGIN_REDIRECT_URL = "/dashboard/"
LOGIN_URL = "/login/"
LOGOUT_REDIRECT_URL = "/"

ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_LOGOUT_ON_GET = False
ACCOUNT_FORMS = {"signup": "acesta.account.forms.SignupForm"}
ACCOUNT_USER_DISPLAY = "acesta.account.utils.user_display"
ACCOUNT_ADAPTER = "acesta.account.adapter.AccountAdapter"
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = False
SOCIALACCOUNT_ADAPTER = "acesta.socialaccount.adapter.SocialAccountAdapter"
SOCIALACCOUNT_AUTO_SIGNUP = False
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_FORMS = {"signup": "acesta.socialaccount.forms.SocialSignupForm"}
LOGOUT_ON_PASSWORD_CHANGE = False
OLD_PASSWORD_FIELD_ENABLED = True

MESSAGE_STORAGE = "django.contrib.messages.storage.cookie.CookieStorage"

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = [
    # https://docs.djangoproject.com/en/dev/topics/auth/passwords/#using-argon2-with-django
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# MIDDLEWARE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.common.BrokenLinkEmailsMiddleware",
    "django_plotly_dash.middleware.BaseMiddleware",
    "django_plotly_dash.middleware.ExternalRedirectionMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "acesta.user.middleware.clean_up_old_periods",
]

# STATIC
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = str(ROOT_DIR / "staticfiles")
# https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = "/static/"
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = [str(APPS_DIR / "static")]
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = str(APPS_DIR / "media")
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "/media/"

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        # https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
        "DIRS": [str(APPS_DIR / "templates")],
        "OPTIONS": {
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
            # https://docs.djangoproject.com/en/dev/ref/templates/api/#loader-types
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "acesta.front.context_processors.settings",
                "acesta.geo.context_processors.settings",
                "acesta.geo.context_processors.regions",
                "acesta.geo.context_processors.user_region_codes",
            ],
        },
    }
]

# https://docs.djangoproject.com/en/dev/ref/settings/#form-renderer
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

# FIXTURES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#fixture-dirs
FIXTURE_DIRS = (str(APPS_DIR / "fixtures"),)

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-httponly
SESSION_COOKIE_HTTPONLY = env.bool("DJANGO_SESSION_COOKIE_HTTPONLY", default=True)
# # https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-httponly
CSRF_COOKIE_HTTPONLY = env.bool("DJANGO_CSRF_COOKIE_HTTPONLY", default=True)
# https://docs.djangoproject.com/en/dev/ref/settings/#x-frame-options
X_FRAME_OPTIONS = env("DJANGO_X_FRAME_OPTIONS", default="DENY")

# EMAIL
# ------------------------------------------------------------------------------
DEFAULT_FROM_EMAIL = env("DJANGO_DEFAULT_FROM_EMAIL", default="")
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# https://docs.djangoproject.com/en/dev/ref/settings/#email-timeout
EMAIL_TIMEOUT = 5
# Host for sending e-mail.
EMAIL_HOST = env("DJANGO_EMAIL_HOST", default="")
# Port for sending e-mail.
EMAIL_PORT = env("DJANGO_EMAIL_PORT", default="")
# Optional SMTP authentication information for EMAIL_HOST.
EMAIL_HOST_USER = env("DJANGO_EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("DJANGO_EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env("DJANGO_EMAIL_USE_TLS", default="")

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL.
ADMIN_URL = env("DJANGO_ADMIN_URL", default="admin/")
# https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = getaddresses([env("DJANGO_ADMINS")])
# https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS
# Django Admin Title
ADMIN_TITLE = "acesta"

# DB_MUTEX
# ------------------------------------------------------------------------------
DB_MUTEX_TTL_SECONDS = 9 * 60 * 60

# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s "
            "%(process)d %(thread)d %(message)s"
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}

# DADATA
DADATA_TOKEN = env("API_DADATA_TOKEN", default="")
DADATA_SECRET = env("API_DADATA_SECRET", default="")

# Application
TITLE = "Аналитика в туризме — ацеста"
HASH_TAGS = "#туризм #аналитика"

GEOJSON = ROOT_DIR / "geojson" / "Russia.geojson"

RATING_TYPE_AMOUNT = "amount"
RATING_TYPE_POPULARITY = "popularity"
RATING_TYPE_QUERIES = "queries"

RATING_TYPES = (
    (RATING_TYPE_AMOUNT, "Количество точек притяжения"),
    (RATING_TYPE_POPULARITY, "Региональная популярность"),
    (RATING_TYPE_QUERIES, "Количество запросов"),
)

RATING_TYPE_DEFAULT = "amount"

SALARY_TYPES = (
    ("average_salary", "Средняя зарплата"),
    ("average_per_person", "Средний доход на человека"),
)

SALARY_TYPE_DEFAULT = "average_salary"

STATE_NEW = "new"
STATE_WAITING = "waiting"
STATE_PAID = "paid"
STATE_CANCELED = "canceled"
STATE_DONE = "done"

SUPPORT_QUESTION = "support"
SUPPORT_REPORT = "report"
SUPPORT_SIGHTS = "sights"

SUPPORT_SUBJECTS = (
    (SUPPORT_QUESTION, "Обращение в техподдержку"),
    (SUPPORT_REPORT, "Заказ отчета"),
    (SUPPORT_SIGHTS, "Новые достопримечательности"),
)

REGION_TYPE_FEDERAL_CITY = "federal_city"

REGION_TYPES = (
    ("kray", "Край"),
    ("region", "Область"),
    ("republic", "Республика"),
    (REGION_TYPE_FEDERAL_CITY, "Город федерального значения"),
    ("autonomous_district", "Автономный округ"),
    ("autonomous_region", "Автономная область"),
)

AREA_REGIONS = "regions"
AREA_CITIES = "cities"
AREA_SIGHTS = "sights"

AGE = (
    ("18-24", "от 18 до 24 лет"),
    ("25-29", "от 25 до 29 лет"),
    ("30-34", "от 30 до 34 лет"),
    ("35-44", "от 35 до 44 лет"),
    ("45-80", "от 45 до 80 лет"),
)
SEX = (
    ("w", "Женщины"),
    ("m", "Мужчины"),
)

TOURISM_TYPES = tuple(
    map(
        lambda x: tuple(x.split("=")),
        env.list("ACESTA_TOURISM_TYPES", default=()),
    )
) or (("museum", "музейный туризм"),)

TOURISM_TYPE_DEFAULT = env("ACESTA_TOURISM_TYPE_DEFAULT", default="museum")

PRICES = {k: int(v) for k, v in env.dict("ACESTA_PRICES", default={}).items()}

TOURISM_TYPE_PALETTE = env.dict("ACESTA_TOURISM_TYPE_PALETTE", default={})

SIGHT_GROUPS_PALETTE = env.dict("ACESTA_SIGHT_GROUPS_PALETTE", default={})
