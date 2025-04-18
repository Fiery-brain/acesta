# Generated by Django 3.2.16 on 2023-03-04 15:18

import datetime
from django.db import migrations, models

# from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ("stats", "0005_rename_updates_update"),
    ]

    operations = [
        migrations.AddField(
            model_name="update",
            name="plan",
            field=models.DateField(
                default=datetime.datetime(2023, 3, 4, 15, 18, 21, 697304),  # , tzinfo=utc
                verbose_name="Плановая дата следующего обновления",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="update",
            name="date",
            field=models.DateField(verbose_name="Дата обновления"),
        ),
    ]
