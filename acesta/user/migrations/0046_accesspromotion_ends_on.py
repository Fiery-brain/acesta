import calendar
from datetime import date

from django.db import migrations
from django.db import models
from django.utils import timezone


def set_access_promotion_end_dates(apps, schema_editor):
    AccessPromotion = apps.get_model("user", "AccessPromotion")
    for promotion in AccessPromotion.objects.all().only("id", "modified"):
        modified = timezone.localtime(promotion.modified).date()
        promotion.ends_on = date(
            modified.year,
            modified.month,
            calendar.monthrange(modified.year, modified.month)[1],
        )
        promotion.save(update_fields=("ends_on",))


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0045_enable_api_by_default"),
    ]

    operations = [
        migrations.AddField(
            model_name="accesspromotion",
            name="ends_on",
            field=models.DateField(editable=False, null=True, verbose_name="Действует до"),
        ),
        migrations.RunPython(set_access_promotion_end_dates, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="accesspromotion",
            name="ends_on",
            field=models.DateField(editable=False, verbose_name="Действует до"),
        ),
    ]
