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
TESTING = False
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
]

LOCAL_APPS = [
    "acesta.base",
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
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 6},
    },
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
    "django_plotly_dash.middleware.BaseMiddleware",
    "django_plotly_dash.middleware.ExternalRedirectionMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "acesta.user.middleware.clean_up_old_periods",
    "acesta.user.middleware.set_last_hit",
    "acesta.user.middleware.check_registered",
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
    "django_plotly_dash.finders.DashAssetFinder",
    "django_plotly_dash.finders.DashComponentFinder",
    "django_plotly_dash.finders.DashAppDirectoryFinder",
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
                "acesta.base.context_processors.host",
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
EMAIL_USE_TLS = env("DJANGO_EMAIL_USE_TLS", default=False)
EMAIL_USE_SSL = env("DJANGO_EMAIL_USE_SSL", default=False)
EMAIL_SUBJECT_PREFIX = "ацеста. "

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL.
ADMIN_URL = env("DJANGO_ADMIN_URL", default="admin/")
# https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = getaddresses([env("DJANGO_ADMINS", default="")])
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
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}

# DADATA
DADATA_TOKEN = env("API_DADATA_TOKEN", default="")
DADATA_SECRET = env("API_DADATA_SECRET", default="")

# Application
TITLE = "ацеста"
HASH_TAGS = "#туризм #ии #данные #аналитика"

DEFAULT_SEGMENT = "undefined"
SEGMENT_GOVERNMENT = "government"
SEGMENT_TIC = "tic"
SEGMENT_TOUR_OPERATOR = "tour-operator"
SEGMENT_TOUR_AGENT = "tour-agent"
SEGMENT_TOURISM_PRODUCT_OWNER = "tourism-product-owner"
SEGMENT_INVESTORS = "tourist-investor"
SEGMENT_GUIDE = "tourist-guide"
SEGMENT_MARKETING_AGENCY = "marketing-agency"
SEGMENT_HOSPITALITY = "hospitality"
SEGMENT_TOURISM_EVENT = "tourism-event"
SEGMENT_TRANSPORTATION = "transportation"

SEGMENTS = tuple((k, v) for k, v in env.dict("ACESTA_SEGMENTS", default={}).items())

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

AVERAGE_SALARY = "average_salary"
AVERAGE_BILL = "average_bill"
AVERAGE_PER_PERSON = "average_per_person"

SALARY_TYPES = (
    (AVERAGE_SALARY, "Средняя начисленная зарплата"),
    (AVERAGE_BILL, "Средний чек"),
    (AVERAGE_PER_PERSON, "Средний доход на человека"),
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

REQUEST_CONSULTATION = "consultation"
REQUEST_PRESENTATION = "presentation"

REQUEST_SUBJECTS = (
    (REQUEST_CONSULTATION, "Консультация"),
    (REQUEST_PRESENTATION, "Презентация"),
)

CHANNEL_PHONE = "phone"
CHANNEL_TELEGRAM = "telegram"
CHANNEL_WHATSAPP = "whatsapp"
CHANNEL_VIBER = "viber"
CHANNEL_VK = "vk"
CHANNEL_FB = "facebook"
CHANNEL_EMAIL = "email"

REQUEST_CHANNELS = (
    (CHANNEL_PHONE, "Телефон"),
    (CHANNEL_TELEGRAM, "Telegram"),
    (CHANNEL_WHATSAPP, "WhatsApp"),
    (CHANNEL_VIBER, "Viber"),
    (CHANNEL_VK, "VK"),
    (CHANNEL_FB, "Facebook"),
    (CHANNEL_EMAIL, "Email"),
)

REQUEST_CHANNELS_OUTSIDE = (
    (CHANNEL_PHONE, "Телефон"),
    (CHANNEL_TELEGRAM, "Telegram"),
    (CHANNEL_WHATSAPP, "WhatsApp"),
    (CHANNEL_VIBER, "Viber"),
)

FEDERAL_DISTRICTS = (
    ("ЦФО", "Центральный"),
    ("СЗФО", "Северо-Западный"),
    ("ЮФО", "Южный"),
    ("СКФО", "Северо-Кавказский"),
    ("ПФО", "Приволжский"),
    ("УрФО", "Уральский"),
    ("СФО", "Сибирский"),
    ("ДФО", "Дальневосточный"),
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

PART_REGION = "region"
PART_INTEREST = "interest"
PART_RATING = "rating"

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

PERIOD_DATE_FORMAT = "%d.%m.%Y %H:%M:%S %z"
TOURISM_TYPE_COEF = env("ACESTA_TOURISM_TYPE_COEF", default=0.27)
PERIOD_1_WEEK_COEF = env("ACESTA_PERIOD_1_WEEK_COEF", default=0.35)
PERIOD_2_WEEKS_COEF = env("ACESTA_PERIOD_2_WEEKS_COEF", default=0.6)
ORDER_PERIODS = (
    (0.25, "1 неделя"),
    (0.5, "2 недели"),
    (1.0, "1 месяц"),
    (2.0, "2 месяца"),
    (3.0, "3 месяца"),
    (4.0, "4 месяца"),
    (5.0, "5 месяцев"),
    (6.0, "6 месяцев"),
    (12.0, "12 месяцев"),
)

TOURISM_TYPES_OUTSIDE = tuple((k, v) for k, v in TOURISM_TYPES)

TOURISM_TYPE_DEFAULT = env("ACESTA_TOURISM_TYPE_DEFAULT", default="museum")

PRICES = {k: int(v) for k, v in env.dict("ACESTA_PRICES", default={}).items()}

TOURISM_TYPE_PALETTE = env.dict("ACESTA_TOURISM_TYPE_PALETTE", default={})

SIGHT_GROUPS_PALETTE = env.dict("ACESTA_SIGHT_GROUPS_PALETTE", default={})

SEGMENTS_GENITIVE = env.dict("ACESTA_SEGMENTS_GENITIVE", default={})

SEGMENTS_GENITIVE_SHORT = env.dict("ACESTA_SEGMENTS_GENITIVE_SHORT", default={})

RECOMMENDATION_TOV = env.dict("ACESTA_RECOMMENDATION_TOV", default={})

RECOMMENDATION_NOTE = env.dict("ACESTA_RECOMMENDATION_NOTE", default={})

RECOMMENDATION_RULES = env("ACESTA_RECOMMENDATION_RULES", default="")

REGION_RECOMMENDATION_TEMPLATE = env(
    "ACESTA_REGION_RECOMMENDATION_TEMPLATE", default=""
)

INTEREST_RECOMMENDATION_TEMPLATE = env(
    "ACESTA_INTEREST_RECOMMENDATION_TEMPLATE", default=""
)

AUDIENCE_RECOMMENDATION_TEMPLATE = env(
    "ACESTA_AUDIENCE_RECOMMENDATION_TEMPLATE", default=""
)

AUDIENCE_SEGMENT_RECOMMENDATION_TEMPLATE = env(
    "ACESTA_AUDIENCE_SEGMENT_RECOMMENDATION_TEMPLATE", default=""
)

RATING_RECOMMENDATION_TEMPLATE = env(
    "ACESTA_RATING_RECOMMENDATION_TEMPLATE", default=""
)

LLM_MODELS = env.list("ACESTA_LLM_MODELS", default=[])
LLM_PROVIDERS = env.list("ACESTA_LLM_PROVIDERS", default=[])
LLM_MAX_RETRIES = env.int("ACESTA_LLM_MAX_RETRIES", default=3)
LLM_BASE_DELAY = env.float("ACESTA_LLM_BASE_DELAY", default=1.0)
