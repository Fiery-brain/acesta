from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("stats", "0020_allregionpopularity_covering_index"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="sightrating",
            index=models.Index(
                fields=["rating_type", "place"],
                name="stats_sight_global_top_idx",
                condition=models.Q(
                    region_code__isnull=True,
                    sight_group__isnull=True,
                ),
            ),
        ),
    ]
