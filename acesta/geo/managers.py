from django.db import models


class PubManager(models.Manager):
    """
    Менеджер для выбора только опубликованных записей
    """

    def get_queryset(self):
        return super().get_queryset().filter(is_pub=True)
