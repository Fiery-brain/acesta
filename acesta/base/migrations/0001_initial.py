# Generated manually for base process registry.

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ProcessRegistry",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("domain", models.CharField(db_index=True, max_length=50)),
                ("process", models.CharField(db_index=True, max_length=100)),
                (
                    "key",
                    models.CharField(db_index=True, max_length=255, unique=True),
                ),
                ("data", models.JSONField(blank=True, default=dict)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("modified", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Реестр процесса",
                "verbose_name_plural": "Реестр процессов",
                "ordering": ("domain", "process", "key"),
            },
        ),
    ]
