# Generated by Django 3.2.16 on 2023-07-04 16:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0009_alter_request_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='request',
            name='state',
            field=models.CharField(choices=[('new', 'новый'), ('waiting', 'в ожидании'), ('done', 'обработан')], default='new', max_length=10, verbose_name='Статус'),
        ),
    ]