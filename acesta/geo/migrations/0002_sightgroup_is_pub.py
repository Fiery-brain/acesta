# Generated by Django 3.2.16 on 2023-03-04 10:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sightgroup',
            name='is_pub',
            field=models.BooleanField(db_index=True, default=False, verbose_name='Публиковать'),
        ),
    ]