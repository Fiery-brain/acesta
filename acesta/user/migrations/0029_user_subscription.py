# Generated by Django 3.2.16 on 2023-07-29 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0028_auto_20230729_1449'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='subscription',
            field=models.BooleanField(default=1, verbose_name='Подписка на новости'),
        ),
    ]
