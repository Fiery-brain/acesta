from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [("user", "0043_alter_support_subject")]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_api_enabled",
            field=models.BooleanField(default=False, verbose_name="Доступ к API"),
        ),
    ]
