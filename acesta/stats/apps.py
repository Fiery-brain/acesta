from django.apps import AppConfig


class StatsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "acesta.stats"
    verbose_name = "Статистика"


dash_args = dict(update_title="Загрузка...")
