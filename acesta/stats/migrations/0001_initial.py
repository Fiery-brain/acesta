# Generated by Django 3.2.16 on 2023-02-10 03:30

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('geo', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SightRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('history', models.JSONField(default=list, max_length=2500, verbose_name='История')),
                ('date', models.DateField(auto_now=True, verbose_name='Дата')),
                ('rating_type', models.CharField(choices=[('amount', 'Количество точек притяжения'), ('popularity', 'Региональная популярность'), ('queries', 'Количество запросов')], default='amount', max_length=10, verbose_name='Вид рейтинга')),
                ('place', models.IntegerField(default=0, verbose_name='Место')),
                ('value', models.IntegerField(blank=True, default=0, null=True, verbose_name='Значение')),
                ('city_code', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sightrating_cities', to='geo.city', verbose_name='Город-интересант')),
                ('region_code', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sightrating_regions', to='geo.region', verbose_name='Регион-интересант')),
                ('sight', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sightrating_sights', to='geo.sight', verbose_name='Достопримечательность')),
                ('sight_group', models.ForeignKey(blank=True, max_length=15, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='geo.sightgroup', verbose_name='Вид достопримечательности')),
            ],
            options={
                'verbose_name': 'Рейтинг достопримечательностей',
                'verbose_name_plural': 'Рейтинг достопримечательностей',
                'ordering': ('rating_type', 'place'),
            },
        ),
        migrations.CreateModel(
            name='Salary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('value_type', models.CharField(choices=[('average_salary', 'Средняя зарплата'), ('average_per_capita_income', 'Средний доход на душу населения')], default='average_salary', max_length=30, verbose_name='Вид показателя')),
                ('quarter', models.PositiveSmallIntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4)], verbose_name='Квартал')),
                ('year', models.PositiveSmallIntegerField(choices=[(2019, 2019), (2020, 2020), (2021, 2021), (2022, 2022), (2023, 2023), (2024, 2024), (2025, 2025), (2026, 2026), (2027, 2027), (2028, 2028), (2029, 2029), (2030, 2030)], verbose_name='Год')),
                ('value', models.FloatField(default=0.0, verbose_name='Значение')),
                ('code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='salary_codes', to='geo.region', verbose_name='Регион')),
            ],
            options={
                'verbose_name': 'Доходы',
                'verbose_name_plural': 'Доходы',
                'ordering': ('-year', '-quarter', 'code'),
            },
        ),
        migrations.CreateModel(
            name='RegionRegionPopularity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('history', models.JSONField(default=list, max_length=2500, verbose_name='История')),
                ('date', models.DateTimeField(auto_now=True, verbose_name='Дата')),
                ('qty', models.IntegerField(db_index=True, default=0, help_text='Среднее число показов в месяц', verbose_name='Показы')),
                ('popularity_mean_all', models.FloatField(default=0, help_text='Средняя региональная популярность в геообъекте по всем запросам', verbose_name='Популярность')),
                ('popularity_mean', models.FloatField(default=0, help_text='Средняя региональная популярность в геообъекте только по запросам, вызвавшим интерес', verbose_name='Популярность > 100')),
                ('popularity_max', models.FloatField(default=0, help_text='Максимальная региональная популярность в геообъекте', verbose_name='Максимальная популярность')),
                ('tourism_type', models.CharField(blank=True, choices=[('museum', 'музейный туризм'), ('spa', 'оздоровительный туризм'), ('beach', 'пляжный туризм'), ('outdoor', 'развлекательный туризм'), ('pilgrimage', 'религиозный туризм'), ('extreme', 'спортивный туризм'), ('theatre', 'театральный туризм'), ('shopping', 'шопинг-туризм'), ('recreation', 'экологический туризм'), ('excursion', 'экскурсионный туризм')], db_index=True, max_length=10, null=True, verbose_name='Вид туризма')),
                ('code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='regionregionpopularity_regions', to='geo.region', verbose_name='Интересант')),
                ('home_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='region_region_regions', to='geo.region', verbose_name='Регион')),
            ],
            options={
                'verbose_name': 'Популярность регионов в регионах',
                'verbose_name_plural': 'Популярность регионов в регионах',
                'ordering': ('-qty', 'code'),
            },
        ),
        migrations.CreateModel(
            name='RegionRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('history', models.JSONField(default=list, max_length=2500, verbose_name='История')),
                ('tourism_type', models.CharField(blank=True, choices=[('museum', 'музейный туризм'), ('spa', 'оздоровительный туризм'), ('beach', 'пляжный туризм'), ('outdoor', 'развлекательный туризм'), ('pilgrimage', 'религиозный туризм'), ('extreme', 'спортивный туризм'), ('theatre', 'театральный туризм'), ('shopping', 'шопинг-туризм'), ('recreation', 'экологический туризм'), ('excursion', 'экскурсионный туризм')], db_index=True, max_length=10, null=True, verbose_name='Вид туризма')),
                ('date', models.DateField(auto_now=True, verbose_name='Дата')),
                ('rating_type', models.CharField(choices=[('amount', 'Количество точек притяжения'), ('popularity', 'Региональная популярность'), ('queries', 'Количество запросов')], default='amount', max_length=10, verbose_name='Вид рейтинга')),
                ('place', models.IntegerField(default=0, verbose_name='Место')),
                ('value', models.IntegerField(blank=True, default=0, null=True, verbose_name='Значение')),
                ('city_code', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='regionrating_cities', to='geo.city', verbose_name='Город-интересант')),
                ('home_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='regionrating_home_regions', to='geo.region', verbose_name='Домашний регион')),
                ('region_code', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='regionrating_regions', to='geo.region', verbose_name='Регион-интересант')),
            ],
            options={
                'verbose_name': 'Рейтинг регионов',
                'verbose_name_plural': 'Рейтинг регионов',
                'ordering': ('rating_type', 'place'),
            },
        ),
        migrations.CreateModel(
            name='RegionCityPopularity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('history', models.JSONField(default=list, max_length=2500, verbose_name='История')),
                ('date', models.DateTimeField(auto_now=True, verbose_name='Дата')),
                ('qty', models.IntegerField(db_index=True, default=0, help_text='Среднее число показов в месяц', verbose_name='Показы')),
                ('popularity_mean_all', models.FloatField(default=0, help_text='Средняя региональная популярность в геообъекте по всем запросам', verbose_name='Популярность')),
                ('popularity_mean', models.FloatField(default=0, help_text='Средняя региональная популярность в геообъекте только по запросам, вызвавшим интерес', verbose_name='Популярность > 100')),
                ('popularity_max', models.FloatField(default=0, help_text='Максимальная региональная популярность в геообъекте', verbose_name='Максимальная популярность')),
                ('tourism_type', models.CharField(blank=True, choices=[('museum', 'музейный туризм'), ('spa', 'оздоровительный туризм'), ('beach', 'пляжный туризм'), ('outdoor', 'развлекательный туризм'), ('pilgrimage', 'религиозный туризм'), ('extreme', 'спортивный туризм'), ('theatre', 'театральный туризм'), ('shopping', 'шопинг-туризм'), ('recreation', 'экологический туризм'), ('excursion', 'экскурсионный туризм')], db_index=True, max_length=10, null=True, verbose_name='Вид туризма')),
                ('code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='regioncitypopularity_cities', to='geo.city', verbose_name='Интересант')),
                ('home_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='region_city_regions', to='geo.region', verbose_name='Регион')),
            ],
            options={
                'verbose_name': 'Популярность регионов в городах',
                'verbose_name_plural': 'Популярность регионов в городах',
                'ordering': ('-qty', 'code'),
            },
        ),
        migrations.CreateModel(
            name='CityRegionPopularity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('history', models.JSONField(default=list, max_length=2500, verbose_name='История')),
                ('date', models.DateTimeField(auto_now=True, verbose_name='Дата')),
                ('qty', models.IntegerField(db_index=True, default=0, help_text='Среднее число показов в месяц', verbose_name='Показы')),
                ('popularity_mean_all', models.FloatField(default=0, help_text='Средняя региональная популярность в геообъекте по всем запросам', verbose_name='Популярность')),
                ('popularity_mean', models.FloatField(default=0, help_text='Средняя региональная популярность в геообъекте только по запросам, вызвавшим интерес', verbose_name='Популярность > 100')),
                ('popularity_max', models.FloatField(default=0, help_text='Максимальная региональная популярность в геообъекте', verbose_name='Максимальная популярность')),
                ('tourism_type', models.CharField(blank=True, choices=[('museum', 'музейный туризм'), ('spa', 'оздоровительный туризм'), ('beach', 'пляжный туризм'), ('outdoor', 'развлекательный туризм'), ('pilgrimage', 'религиозный туризм'), ('extreme', 'спортивный туризм'), ('theatre', 'театральный туризм'), ('shopping', 'шопинг-туризм'), ('recreation', 'экологический туризм'), ('excursion', 'экскурсионный туризм')], db_index=True, max_length=10, null=True, verbose_name='Вид туризма')),
                ('code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cityregionpopularity_regions', to='geo.region', verbose_name='Интересант')),
                ('home_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='city_region_cities', to='geo.city', verbose_name='Город')),
            ],
            options={
                'verbose_name': 'Популярность городов в регионах',
                'verbose_name_plural': 'Популярность городов в регионах',
                'ordering': ('-qty', 'code'),
            },
        ),
        migrations.CreateModel(
            name='CityRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('history', models.JSONField(default=list, max_length=2500, verbose_name='История')),
                ('tourism_type', models.CharField(blank=True, choices=[('museum', 'музейный туризм'), ('spa', 'оздоровительный туризм'), ('beach', 'пляжный туризм'), ('outdoor', 'развлекательный туризм'), ('pilgrimage', 'религиозный туризм'), ('extreme', 'спортивный туризм'), ('theatre', 'театральный туризм'), ('shopping', 'шопинг-туризм'), ('recreation', 'экологический туризм'), ('excursion', 'экскурсионный туризм')], db_index=True, max_length=10, null=True, verbose_name='Вид туризма')),
                ('date', models.DateField(auto_now=True, verbose_name='Дата')),
                ('rating_type', models.CharField(choices=[('amount', 'Количество точек притяжения'), ('popularity', 'Региональная популярность'), ('queries', 'Количество запросов')], default='amount', max_length=10, verbose_name='Вид рейтинга')),
                ('place', models.IntegerField(default=0, verbose_name='Место')),
                ('value', models.IntegerField(blank=True, default=0, null=True, verbose_name='Значение')),
                ('city_code', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cityrating_cities', to='geo.city', verbose_name='Город-интересант')),
                ('home_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cityrating_home_cities', to='geo.city', verbose_name='Домашний город')),
                ('home_region', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cityrating_home_regions', to='geo.region', verbose_name='Домашний регион')),
                ('region_code', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cityrating_regions', to='geo.region', verbose_name='Регион-интересант')),
            ],
            options={
                'verbose_name': 'Рейтинг городов',
                'verbose_name_plural': 'Рейтинг городов',
                'ordering': ('rating_type', 'place'),
            },
        ),
        migrations.CreateModel(
            name='CityCityPopularity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('history', models.JSONField(default=list, max_length=2500, verbose_name='История')),
                ('date', models.DateTimeField(auto_now=True, verbose_name='Дата')),
                ('qty', models.IntegerField(db_index=True, default=0, help_text='Среднее число показов в месяц', verbose_name='Показы')),
                ('popularity_mean_all', models.FloatField(default=0, help_text='Средняя региональная популярность в геообъекте по всем запросам', verbose_name='Популярность')),
                ('popularity_mean', models.FloatField(default=0, help_text='Средняя региональная популярность в геообъекте только по запросам, вызвавшим интерес', verbose_name='Популярность > 100')),
                ('popularity_max', models.FloatField(default=0, help_text='Максимальная региональная популярность в геообъекте', verbose_name='Максимальная популярность')),
                ('tourism_type', models.CharField(blank=True, choices=[('museum', 'музейный туризм'), ('spa', 'оздоровительный туризм'), ('beach', 'пляжный туризм'), ('outdoor', 'развлекательный туризм'), ('pilgrimage', 'религиозный туризм'), ('extreme', 'спортивный туризм'), ('theatre', 'театральный туризм'), ('shopping', 'шопинг-туризм'), ('recreation', 'экологический туризм'), ('excursion', 'экскурсионный туризм')], db_index=True, max_length=10, null=True, verbose_name='Вид туризма')),
                ('code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='citycitypopularity_cities', to='geo.city', verbose_name='Интересант')),
                ('home_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='city_city_cities', to='geo.city', verbose_name='Город')),
            ],
            options={
                'verbose_name': 'Популярность городов в городах',
                'verbose_name_plural': 'Популярность городов в городах',
                'ordering': ('-qty', 'code'),
            },
        ),
        migrations.CreateModel(
            name='AudienceRegions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('history', models.JSONField(default=list, max_length=2500, verbose_name='История')),
                ('tourism_type', models.CharField(blank=True, choices=[('museum', 'музейный туризм'), ('spa', 'оздоровительный туризм'), ('beach', 'пляжный туризм'), ('outdoor', 'развлекательный туризм'), ('pilgrimage', 'религиозный туризм'), ('extreme', 'спортивный туризм'), ('theatre', 'театральный туризм'), ('shopping', 'шопинг-туризм'), ('recreation', 'экологический туризм'), ('excursion', 'экскурсионный туризм')], db_index=True, max_length=10, null=True, verbose_name='Вид туризма')),
                ('date', models.DateField(auto_now=True)),
                ('sex', models.CharField(choices=[('w', 'Женщины'), ('m', 'Мужчины')], max_length=1, verbose_name='Пол')),
                ('age', models.CharField(choices=[('18-24', 'от 18 до 24 лет'), ('25-29', 'от 25 до 29 лет'), ('30-34', 'от 30 до 34 лет'), ('35-44', 'от 35 до 44 лет'), ('45-80', 'от 45 до 80 лет')], max_length=5, verbose_name='Возраст')),
                ('v_all', models.IntegerField(default=0, verbose_name='Общее число по региону')),
                ('v_types', models.IntegerField(default=0, verbose_name='Общее число заинтересованных в туризме')),
                ('v_type_sex_age', models.IntegerField(default=0, verbose_name='Заинтересованные, разбивка: вид туризма, пол, возраст')),
                ('v_sex_age', models.IntegerField(default=0, verbose_name='Число определенного пола и возраста')),
                ('v_sex_age_child_6', models.IntegerField(default=0, verbose_name='Число определенного пола и возраста с детьми до 6 лет')),
                ('v_sex_age_child_7_12', models.IntegerField(default=0, verbose_name='Число определенного пола и возраста с детьми от 7 до 12 лет')),
                ('v_sex_age_parents', models.IntegerField(default=0, verbose_name='Число определенного пола и возраста с родителями')),
                ('v_type_in_pair', models.IntegerField(default=0, verbose_name='Число определенного пола и возраста с интересом к виду туризма и в паре')),
                ('coeff', models.FloatField(default=1, verbose_name='Восстанавливающий коэффициент')),
                ('code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='region_audience', to='geo.region', verbose_name='Регион')),
            ],
            options={
                'verbose_name': 'Аудитория в регинах',
                'verbose_name_plural': 'Аудитория в регинах',
            },
        ),
        migrations.CreateModel(
            name='AudienceCities',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('history', models.JSONField(default=list, max_length=2500, verbose_name='История')),
                ('tourism_type', models.CharField(blank=True, choices=[('museum', 'музейный туризм'), ('spa', 'оздоровительный туризм'), ('beach', 'пляжный туризм'), ('outdoor', 'развлекательный туризм'), ('pilgrimage', 'религиозный туризм'), ('extreme', 'спортивный туризм'), ('theatre', 'театральный туризм'), ('shopping', 'шопинг-туризм'), ('recreation', 'экологический туризм'), ('excursion', 'экскурсионный туризм')], db_index=True, max_length=10, null=True, verbose_name='Вид туризма')),
                ('date', models.DateField(auto_now=True)),
                ('sex', models.CharField(choices=[('w', 'Женщины'), ('m', 'Мужчины')], max_length=1, verbose_name='Пол')),
                ('age', models.CharField(choices=[('18-24', 'от 18 до 24 лет'), ('25-29', 'от 25 до 29 лет'), ('30-34', 'от 30 до 34 лет'), ('35-44', 'от 35 до 44 лет'), ('45-80', 'от 45 до 80 лет')], max_length=5, verbose_name='Возраст')),
                ('v_all', models.IntegerField(default=0, verbose_name='Общее число по региону')),
                ('v_types', models.IntegerField(default=0, verbose_name='Общее число заинтересованных в туризме')),
                ('v_type_sex_age', models.IntegerField(default=0, verbose_name='Заинтересованные, разбивка: вид туризма, пол, возраст')),
                ('v_sex_age', models.IntegerField(default=0, verbose_name='Число определенного пола и возраста')),
                ('v_sex_age_child_6', models.IntegerField(default=0, verbose_name='Число определенного пола и возраста с детьми до 6 лет')),
                ('v_sex_age_child_7_12', models.IntegerField(default=0, verbose_name='Число определенного пола и возраста с детьми от 7 до 12 лет')),
                ('v_sex_age_parents', models.IntegerField(default=0, verbose_name='Число определенного пола и возраста с родителями')),
                ('v_type_in_pair', models.IntegerField(default=0, verbose_name='Число определенного пола и возраста с интересом к виду туризма и в паре')),
                ('coeff', models.FloatField(default=1, verbose_name='Восстанавливающий коэффициент')),
                ('code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='city_audience', to='geo.city', verbose_name='Город')),
            ],
            options={
                'verbose_name': 'Аудитория в городах',
                'verbose_name_plural': 'Аудитория в городах',
            },
        ),
        migrations.CreateModel(
            name='AllRegionPopularity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('history', models.JSONField(default=list, max_length=2500, verbose_name='История')),
                ('storage', models.JSONField(default=dict, max_length=2500, verbose_name='Временное хранилище')),
                ('date', models.DateTimeField(auto_now=True, verbose_name='Дата')),
                ('qty', models.IntegerField(db_index=True, default=0, help_text='Среднее число показов в месяц', verbose_name='Показы')),
                ('popularity_mean_all', models.FloatField(default=0, help_text='Средняя региональная популярность в геообъекте по всем запросам', verbose_name='Популярность')),
                ('popularity_mean', models.FloatField(default=0, help_text='Средняя региональная популярность в геообъекте только по запросам, вызвавшим интерес', verbose_name='Популярность > 100')),
                ('popularity_max', models.FloatField(default=0, help_text='Максимальная региональная популярность в геообъекте', verbose_name='Максимальная популярность')),
                ('code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='allregionpopularity_regions', to='geo.region', verbose_name='Интересант')),
                ('home_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='region_all_regions', to='geo.region', verbose_name='Регион')),
                ('sight', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sight_region_sights', to='geo.sight', verbose_name='Достопримечательность')),
                ('sight_group', models.ForeignKey(blank=True, max_length=15, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='geo.sightgroup', verbose_name='Вид достопримечательности')),
                ('source_city', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pp_all_cities', to='geo.city', verbose_name='Город-источник')),
            ],
            options={
                'verbose_name': 'Вся популярность в регионах',
                'verbose_name_plural': 'Вся популярность в регионах',
                'ordering': ('-qty',),
            },
        ),
        migrations.CreateModel(
            name='AllCityPopularity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('history', models.JSONField(default=list, max_length=2500, verbose_name='История')),
                ('storage', models.JSONField(default=dict, max_length=2500, verbose_name='Временное хранилище')),
                ('date', models.DateTimeField(auto_now=True, verbose_name='Дата')),
                ('qty', models.IntegerField(db_index=True, default=0, help_text='Среднее число показов в месяц', verbose_name='Показы')),
                ('popularity_mean_all', models.FloatField(default=0, help_text='Средняя региональная популярность в геообъекте по всем запросам', verbose_name='Популярность')),
                ('popularity_mean', models.FloatField(default=0, help_text='Средняя региональная популярность в геообъекте только по запросам, вызвавшим интерес', verbose_name='Популярность > 100')),
                ('popularity_max', models.FloatField(default=0, help_text='Максимальная региональная популярность в геообъекте', verbose_name='Максимальная популярность')),
                ('code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='allcitypopularity_cities', to='geo.city', verbose_name='Интересант')),
                ('home_code', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='city_all_cities', to='geo.city', verbose_name='Город')),
                ('sight', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sight_city_sights', to='geo.sight', verbose_name='Достопримечательность')),
                ('sight_group', models.ForeignKey(blank=True, max_length=15, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='geo.sightgroup', verbose_name='Вид достопримечательности')),
                ('source_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pp_all_regions', to='geo.region', verbose_name='Регион-источник')),
            ],
            options={
                'verbose_name': 'Вся популярность в городах',
                'verbose_name_plural': 'Вся популярность в городах',
                'ordering': ('-qty',),
            },
        ),
        migrations.AddIndex(
            model_name='sightrating',
            index=models.Index(fields=['region_code', 'sight_group', 'rating_type', 'place'], name='stats_sight_region__263acb_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='sightrating',
            unique_together={('rating_type', 'sight', 'region_code', 'city_code')},
        ),
        migrations.AddIndex(
            model_name='salary',
            index=models.Index(fields=['value_type', 'quarter', 'year'], name='stats_salar_value_t_8e9015_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='salary',
            unique_together={('code', 'value_type', 'quarter', 'year')},
        ),
        migrations.AddIndex(
            model_name='regionregionpopularity',
            index=models.Index(fields=['home_code', 'tourism_type', 'qty', 'code'], name='stats_regio_home_co_451373_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='regionregionpopularity',
            unique_together={('home_code', 'code', 'tourism_type')},
        ),
        migrations.AddIndex(
            model_name='regionrating',
            index=models.Index(fields=['region_code', 'tourism_type', 'rating_type', 'place'], name='stats_regio_region__11ab50_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='regionrating',
            unique_together={('rating_type', 'home_code', 'region_code', 'city_code')},
        ),
        migrations.AddIndex(
            model_name='regioncitypopularity',
            index=models.Index(fields=['home_code', 'tourism_type', 'qty', 'code'], name='stats_regio_home_co_b1e39c_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='regioncitypopularity',
            unique_together={('home_code', 'code', 'tourism_type')},
        ),
        migrations.AddIndex(
            model_name='cityregionpopularity',
            index=models.Index(fields=['home_code', 'tourism_type', 'qty', 'code'], name='stats_cityr_home_co_9b425a_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='cityregionpopularity',
            unique_together={('home_code', 'code', 'tourism_type')},
        ),
        migrations.AddIndex(
            model_name='cityrating',
            index=models.Index(fields=['home_region', 'tourism_type', 'rating_type', 'place'], name='stats_cityr_home_re_192c2c_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='cityrating',
            unique_together={('rating_type', 'home_code', 'region_code', 'city_code')},
        ),
        migrations.AddIndex(
            model_name='citycitypopularity',
            index=models.Index(fields=['home_code', 'tourism_type', 'qty', 'code'], name='stats_cityc_home_co_05a324_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='citycitypopularity',
            unique_together={('home_code', 'code', 'tourism_type')},
        ),
        migrations.AddIndex(
            model_name='audienceregions',
            index=models.Index(fields=['code', 'v_type_sex_age'], name='stats_audie_code_id_05107f_idx'),
        ),
        migrations.AddIndex(
            model_name='audienceregions',
            index=models.Index(fields=['code', 'v_type_sex_age', 'tourism_type'], name='stats_audie_code_id_69a0ab_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='audienceregions',
            unique_together={('code', 'sex', 'age', 'tourism_type')},
        ),
        migrations.AddIndex(
            model_name='audiencecities',
            index=models.Index(fields=['code', 'v_type_sex_age'], name='stats_audie_code_id_978ac6_idx'),
        ),
        migrations.AddIndex(
            model_name='audiencecities',
            index=models.Index(fields=['code', 'v_type_sex_age', 'tourism_type'], name='stats_audie_code_id_5aaa5d_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='audiencecities',
            unique_together={('code', 'sex', 'age', 'tourism_type')},
        ),
        migrations.AlterUniqueTogether(
            name='allregionpopularity',
            unique_together={('sight', 'home_code', 'code', 'source_city')},
        ),
        migrations.AlterUniqueTogether(
            name='allcitypopularity',
            unique_together={('sight', 'home_code', 'code', 'source_code')},
        ),
    ]
