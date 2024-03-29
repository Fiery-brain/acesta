# Generated by Django 3.2.16 on 2023-02-10 14:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='allcitypopularity',
            name='modified_storage',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата обновления хранилища'),
        ),
        migrations.AddField(
            model_name='allregionpopularity',
            name='modified_storage',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата обновления хранилища'),
        ),
        migrations.AlterField(
            model_name='allcitypopularity',
            name='date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата'),
        ),
        migrations.AlterField(
            model_name='allregionpopularity',
            name='date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата'),
        ),
        migrations.AlterField(
            model_name='citycitypopularity',
            name='date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата'),
        ),
        migrations.AlterField(
            model_name='cityregionpopularity',
            name='date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата'),
        ),
        migrations.AlterField(
            model_name='regioncitypopularity',
            name='date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата'),
        ),
        migrations.AlterField(
            model_name='regionregionpopularity',
            name='date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата'),
        ),
    ]
