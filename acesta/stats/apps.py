from django.apps import AppConfig
from django_plotly_dash import DjangoDash


class StatsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "acesta.stats"
    verbose_name = "Статистика"


class AcestaDjangoDash(DjangoDash):
    def __init__(self, *args, update_title="Загрузка...", **kwargs):
        super().__init__(*args, **kwargs)
        self._kwargs["update_title"] = update_title
