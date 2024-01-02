from django.apps import AppConfig
from django.conf import settings


class UserConfig(AppConfig):
    name = "acesta.user"
    verbose_name = "Пользователь"
    verbose_name_plural = "Пользователи"


PRICES = {
    "rank_0": 0,
    "rank_1": settings.PRICES.get("rank_1"),
    "rank_2": settings.PRICES.get("rank_2"),
    "rank_3": settings.PRICES.get("rank_3"),
    "rank_4": settings.PRICES.get("rank_4"),
}

DISCOUNTS = {
    "gt_6_discount": settings.PRICES.get("gt_6_discount"),
    "gt_12_discount": settings.PRICES.get("gt_12_discount"),
}
