# Generated by Django 3.2.16 on 2023-07-10 15:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0005_auto_20230423_1451'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sight',
            name='geo_data',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='sight',
            name='kernel',
            field=models.JSONField(blank=True, default=list, max_length=500, verbose_name='Семантическое ядро'),
        ),
        migrations.AlterField(
            model_name='sight',
            name='query',
            field=models.CharField(blank=True, max_length=150, verbose_name='Строка поиска'),
        ),
    ]