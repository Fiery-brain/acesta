# Generated by Django 3.2.16 on 2023-02-10 03:30

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Region',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('code', models.CharField(max_length=2, primary_key=True, serialize=False, verbose_name='Код региона')),
                ('_id', models.IntegerField(unique=True, verbose_name='Внешний ID')),
                ('region', models.CharField(max_length=60, verbose_name='Название региона в Яндекс')),
                ('title', models.CharField(db_index=True, max_length=60, verbose_name='Название региона')),
                ('region_type', models.CharField(choices=[('kray', 'Край'), ('region', 'Область'), ('republic', 'Республика'), ('federal_city', 'Город федерального значения'), ('autonomous_district', 'Автономный округ'), ('autonomous_region', 'Автономная область')], max_length=30, verbose_name='Вид субъекта')),
                ('paths', models.TextField(blank=True, null=True, verbose_name='Контуры')),
                ('polygons', models.TextField(blank=True, null=True, verbose_name='Полигоны')),
                ('rank', models.IntegerField(default=0, verbose_name='Ранг')),
                ('territory', models.IntegerField(default=0, verbose_name='Территория')),
                ('population', models.IntegerField(default=0, verbose_name='Численность')),
                ('zoom_regions', models.FloatField(default=3.5, verbose_name='Zoom')),
                ('zoom_cities', models.FloatField(default=5, verbose_name='Zoom')),
                ('center_lat', models.FloatField(default=69, verbose_name='Center latitude')),
                ('center_lon', models.FloatField(default=105, verbose_name='Center longitude')),
                ('synonyms', models.TextField(blank=True, help_text='Введите фразы отделив их переводом строки', null=True, verbose_name='Синонимы')),
                ('is_pub', models.BooleanField(db_index=True, default=False, verbose_name='Публиковать')),
            ],
            options={
                'verbose_name': 'Регион',
                'verbose_name_plural': 'Регионы',
                'ordering': ('code',),
            },
        ),
        migrations.CreateModel(
            name='SightGroup',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('tourism_type', models.CharField(choices=[('museum', 'музейный туризм'), ('spa', 'оздоровительный туризм'), ('beach', 'пляжный туризм'), ('outdoor', 'развлекательный туризм'), ('pilgrimage', 'религиозный туризм'), ('extreme', 'спортивный туризм'), ('theatre', 'театральный туризм'), ('shopping', 'шопинг-туризм'), ('recreation', 'экологический туризм'), ('excursion', 'экскурсионный туризм')], default='recreation', max_length=10, verbose_name='Вид туризма')),
                ('name', models.CharField(max_length=15, primary_key=True, serialize=False, verbose_name='Имя')),
                ('title', models.CharField(max_length=150, verbose_name='Название')),
                ('title_gen', models.CharField(max_length=150, verbose_name='Название в родительном падеже')),
            ],
            options={
                'verbose_name': 'Группа',
                'verbose_name_plural': 'Группы',
                'ordering': ('title',),
            },
        ),
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('_id', models.IntegerField(unique=True, verbose_name='Внешний ID')),
                ('title', models.CharField(db_index=True, max_length=150, verbose_name='Название')),
                ('area', models.CharField(blank=True, max_length=150, null=True, verbose_name='Район')),
                ('lat', models.FloatField(default=0.0, verbose_name='Широта')),
                ('lon', models.FloatField(default=0.0, verbose_name='Долгота')),
                ('population', models.IntegerField(default=0, verbose_name='Численность')),
                ('foundation', models.CharField(max_length=60, verbose_name='Год основания')),
                ('is_capital', models.BooleanField(default=False, verbose_name='Столица')),
                ('is_pub', models.BooleanField(db_index=True, default=False, verbose_name='Публиковать')),
                ('synonyms', models.TextField(blank=True, help_text='Введите фразы отделив их переводом строки', null=True, verbose_name='Синонимы')),
                ('code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='region_cities', to='geo.region', verbose_name='Регион')),
            ],
            options={
                'verbose_name': 'Город',
                'verbose_name_plural': 'Города',
                'ordering': ('title',),
            },
        ),
        migrations.CreateModel(
            name='Sight',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('title', models.CharField(blank=True, max_length=150, null=True, verbose_name='Название')),
                ('name', models.CharField(blank=True, max_length=150, null=True, verbose_name='Внешнее имя')),
                ('_id', models.IntegerField(blank=True, null=True, verbose_name='Внешний ID')),
                ('full_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Полное внешнее имя')),
                ('query', models.CharField(max_length=150, verbose_name='Строка поиска')),
                ('query_additional', models.CharField(blank=True, help_text='через запятую', max_length=255, null=True, verbose_name='Дополнительные строки поиска')),
                ('kernel', models.JSONField(default=list, max_length=500, verbose_name='Семантическое ядро')),
                ('rate', models.FloatField(default=0.0, verbose_name='Рейтинг')),
                ('stars', models.IntegerField(default=0, verbose_name='Звезды')),
                ('viewings', models.IntegerField(default=0, verbose_name='Количество просмотров')),
                ('lat', models.FloatField(default=0.0, verbose_name='Широта')),
                ('lon', models.FloatField(default=0.0, verbose_name='Долгота')),
                ('address', models.CharField(blank=True, max_length=255, null=True, verbose_name='Адрес')),
                ('_address', models.CharField(blank=True, max_length=255, null=True, verbose_name='Внешний адрес')),
                ('full_link', models.CharField(blank=True, max_length=500, null=True, verbose_name='Ссылка')),
                ('photo', models.CharField(blank=True, max_length=500, null=True, verbose_name='Фото')),
                ('operating_hours', models.CharField(blank=True, max_length=700, null=True, verbose_name='Часы работы')),
                ('operating_hours_data', models.CharField(blank=True, max_length=700, null=True, verbose_name='Дополнительная информация о часах работы')),
                ('is_checked', models.BooleanField(db_index=True, default=False, verbose_name='Запрос проверен')),
                ('modified_kernel', models.DateTimeField(blank=True, null=True, verbose_name='Последнее обновление ядра')),
                ('is_pub', models.BooleanField(db_index=True, default=False, verbose_name='Публиковать')),
                ('is_in_geo_region', models.BooleanField(default=True)),
                ('geo_data', models.JSONField(default=dict)),
                ('city', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sight_cities', to='geo.city', verbose_name='Город')),
                ('code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='region_sights', to='geo.region', verbose_name='Регион')),
                ('group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='sight_groups', to='geo.sightgroup', verbose_name='Группы')),
            ],
            options={
                'verbose_name': 'Достопримечательность',
                'verbose_name_plural': 'Достопримечательности',
                'unique_together': {('name', 'full_name', 'city', 'is_pub', 'code', 'lat', 'lon')},
            },
        ),
    ]
