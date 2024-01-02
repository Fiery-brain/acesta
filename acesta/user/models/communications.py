from django.conf import settings
from django.db import models
from model_utils.models import TimeStampedModel

from acesta.geo.models import Region
from acesta.user.models.user import User
from acesta.user.validators import validate_russian


class Support(TimeStampedModel):
    """
    Support Model
    """

    user = models.ForeignKey(
        User,
        verbose_name="Пользователь",
        on_delete=models.DO_NOTHING,
        related_name="user_messages",
    )
    subject = models.CharField("Тема", max_length=10, choices=settings.SUPPORT_SUBJECTS)
    message = models.TextField(
        "Сообщение",
    )
    state = models.CharField(
        "Статус",
        max_length=10,
        choices=(
            (settings.STATE_NEW, "в обработке"),
            (settings.STATE_DONE, "обработана"),
        ),
        default=settings.STATE_NEW,
    )

    class Meta:
        verbose_name = "Обращение"
        verbose_name_plural = "Обращения"
        ordering = ["-modified"]


class Request(TimeStampedModel):
    """
    Request Model
    """

    name = models.CharField("Имя", max_length=35, validators=[validate_russian])
    user = models.ForeignKey(
        User,
        verbose_name="Пользователь",
        on_delete=models.DO_NOTHING,
        related_name="user_requests",
        blank=True,
        null=True,
    )
    channel = models.CharField(
        "Канал связи", max_length=10, choices=settings.REQUEST_CHANNELS
    )
    _id = models.CharField("Номер или ник", max_length=32)
    subject = models.CharField(
        "Тема",
        max_length=15,
        choices=settings.REQUEST_SUBJECTS,
        default=settings.REQUEST_CONSULTATION,
    )
    time = models.DateTimeField("Срок", blank=True, null=True)
    comment = models.CharField("Комментарий", max_length=255, blank=True, null=True)
    note = models.CharField("Заметки", max_length=255, blank=True, null=True)
    region = models.ForeignKey(
        Region,
        verbose_name="Регион",
        on_delete=models.DO_NOTHING,
        related_name="region_requests",
        blank=True,
        null=True,
    )
    interest = models.BooleanField("Интерес", default=True)
    state = models.CharField(
        "Статус",
        max_length=10,
        choices=(
            (settings.STATE_NEW, "новый"),
            (settings.STATE_WAITING, "в ожидании"),
            (settings.STATE_DONE, "обработан"),
        ),
        default=settings.STATE_NEW,
    )

    class Meta:
        verbose_name = "Запросы"
        verbose_name_plural = "Запросы"
        ordering = ["-modified"]
