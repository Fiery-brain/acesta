from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("geo", "0018_city_description_region_description"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="sight",
            index=models.Index(
                fields=["code", "id"],
                name="geo_sight_pub_code_id_idx",
                condition=models.Q(is_pub=True),
            ),
        ),
    ]
