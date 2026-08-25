from django.db import migrations
from django.db import models


def enable_api_for_existing_users(apps, schema_editor):
    user_model = apps.get_model("user", "User")
    user_model.objects.filter(is_api_enabled=False).update(is_api_enabled=True)


class Migration(migrations.Migration):
    dependencies = [("user", "0044_user_is_api_enabled")]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="is_api_enabled",
            field=models.BooleanField(default=True, verbose_name="Доступ к API"),
        ),
        migrations.RunPython(
            enable_api_for_existing_users,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
