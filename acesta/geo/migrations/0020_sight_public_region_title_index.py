from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("geo", "0019_sight_public_region_index"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="sight",
            index=models.Index(
                fields=["code", "title", "id"],
                name="geo_sight_pub_code_title_idx",
                condition=models.Q(is_pub=True),
            ),
        ),
    ]
