# Generated by Django 3.2.16 on 2023-07-18 15:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0016_auto_20230718_1055'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='company',
            field=models.CharField(blank=True, max_length=130, null=True, verbose_name='Компания'),
        ),
        migrations.AlterField(
            model_name='user',
            name='position',
            field=models.CharField(blank=True, max_length=130, null=True, verbose_name='Должность'),
        ),
    ]