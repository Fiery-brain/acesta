# Generated by Django 3.2.16 on 2023-07-21 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0019_user_note'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='phone',
            field=models.CharField(blank=True, max_length=12, null=True, verbose_name='Телефон'),
        ),
    ]