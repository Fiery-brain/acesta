import calendar
from datetime import date

from django.conf import settings
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from model_utils.models import TimeStampedModel


class AccessPromotion(TimeStampedModel):
    title = models.CharField("Название рекламной кампании", max_length=255)
    discount = models.PositiveSmallIntegerField(
        "Скидка, %",
        validators=(MinValueValidator(1), MaxValueValidator(99)),
    )
    is_active = models.BooleanField("Активна", default=False)
    ends_on = models.DateField("Действует до", editable=False)

    def save(self, *args, **kwargs):
        day = timezone.localdate()
        self.ends_on = date(
            day.year,
            day.month,
            calendar.monthrange(day.year, day.month)[1],
        )
        if kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {"ends_on"}
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Акция на доступ"
        verbose_name_plural = "Акции на доступ"
        ordering = ("-modified",)
        constraints = (
            models.UniqueConstraint(
                fields=("is_active",),
                condition=models.Q(is_active=True),
                name="unique_active_access_promotion",
            ),
        )

    def __str__(self):
        return self.title


class AccessPromotionCode(models.Model):
    promotion = models.ForeignKey(
        AccessPromotion,
        verbose_name="Акция",
        on_delete=models.CASCADE,
        related_name="codes",
    )
    segment = models.CharField(
        "Сегмент",
        max_length=25,
        choices=settings.SEGMENTS,
        default=settings.DEFAULT_SEGMENT,
    )
    code = models.CharField(
        "Код промокода",
        max_length=10,
        validators=(
            RegexValidator(
                regex=r"^[A-Z0-9]{10}$",
                message="Промокод должен состоять ровно из 10 латинских букв и цифр",
            ),
        ),
    )

    class Meta:
        verbose_name = "Промокод акции"
        verbose_name_plural = "Промокоды акции"
        ordering = ("segment",)
        constraints = (
            models.UniqueConstraint(
                fields=("promotion", "segment"),
                name="unique_access_promotion_segment_code",
            ),
            models.CheckConstraint(
                check=models.Q(code__regex=r"^[A-Z0-9]{10}$"),
                name="valid_access_promotion_code",
            ),
        )

    def __str__(self):
        return f"{self.promotion}: {self.segment} — {self.code}"

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        return super().save(*args, **kwargs)
