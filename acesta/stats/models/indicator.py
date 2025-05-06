from django.conf import settings
from django.db import models
from model_utils.models import TimeStampedModel

from acesta.geo.models import Region


class Indicator(TimeStampedModel):
    """
    Regions indicators
    """

    code = models.ForeignKey(
        Region,
        verbose_name="Регион",
        on_delete=models.CASCADE,
        related_name="region_salaries",
    )
    value_type = models.CharField(
        "Вид показателя",
        choices=settings.SALARY_TYPES,
        default=settings.SALARY_TYPE_DEFAULT,
        max_length=30,
    )
    quarter = models.PositiveSmallIntegerField(
        "Квартал", choices=((q, q) for q in range(1, 5))
    )
    month = models.PositiveSmallIntegerField(
        "Месяц", choices=((q, q) for q in range(1, 13)), null=True, blank=True
    )
    year = models.PositiveSmallIntegerField(
        "Год", choices=((y, y) for y in range(2019, 2031, 1))
    )
    value = models.FloatField("Значение", default=0.0)
    change = models.FloatField("Изменение", default=0.0)

    class Meta:
        unique_together = (
            "code",
            "value_type",
            "month",
            "quarter",
            "year",
        )
        indexes = [
            models.Index(fields=["value_type", "quarter", "year"]),
        ]
        ordering = (
            "-year",
            "-quarter",
            "code",
        )
        verbose_name = "Экономические показатели"
        verbose_name_plural = "Экономические показатели"
