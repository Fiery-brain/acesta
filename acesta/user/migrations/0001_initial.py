# Generated by Django 3.2.16 on 2023-02-10 03:30

import acesta.user.models
from django.conf import settings
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('geo', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Email')),
                ('period_info', models.JSONField(blank=True, default=dict, null=True, verbose_name='Периоды полного доступа')),
                ('middle_name', models.CharField(max_length=50, verbose_name='Отчество')),
                ('phone', models.CharField(blank=True, max_length=12, null=True, verbose_name='Телефон')),
                ('company', models.CharField(blank=True, max_length=100, null=True, verbose_name='Компания')),
                ('position', models.CharField(blank=True, max_length=80, null=True, verbose_name='Должность')),
                ('city', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='geo.city', verbose_name='Город')),
                ('current_region', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='current_region_regions', to='geo.region', verbose_name='Последний регион')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('region', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='region_regions', to='geo.region', verbose_name='Домашний регион')),
                ('regions', models.ManyToManyField(blank=True, related_name='user_regions', to='geo.Region', verbose_name='Оплаченные регионы')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'Пользователь',
                'verbose_name_plural': 'Пользователи',
                'ordering': ['-date_joined'],
            },
            managers=[
                ('objects', acesta.user.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('period', models.IntegerField(verbose_name='Период (месяцев)')),
                ('cost', models.DecimalField(decimal_places=2, default=0.0, max_digits=10, verbose_name='Стоимость')),
                ('discount', models.DecimalField(decimal_places=2, default=0.0, max_digits=10, verbose_name='Скидка')),
                ('total', models.DecimalField(decimal_places=2, default=0.0, max_digits=10, verbose_name='Итого')),
                ('begin_time', models.DateTimeField(blank=True, null=True, verbose_name='Дата начала')),
                ('end_time', models.DateTimeField(blank=True, null=True, verbose_name='Дата конца')),
                ('state', models.CharField(choices=[('new', 'в обработке'), ('waiting', 'ожидает оплаты'), ('paid', 'оплачена'), ('canceled', 'отменена'), ('done', 'выполнена')], default='new', max_length=10, verbose_name='Статус')),
                ('regions', models.ManyToManyField(blank=True, related_name='order_regions', to='geo.Region', verbose_name='Регионы')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_orders', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Заявка',
                'verbose_name_plural': 'Заявки',
                'ordering': ['-modified'],
            },
        ),
    ]