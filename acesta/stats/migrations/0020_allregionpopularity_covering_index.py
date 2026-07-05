from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("stats", "0019_alter_allcitypopularity_unique_together"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="allregionpopularity",
            index=models.Index(
                fields=["sight"],
                include=["qty"],
                name="stats_ar_sight_qty_cover",
            ),
        ),
    ]
