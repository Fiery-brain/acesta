# Generated by Django 3.2.16 on 2023-07-25 02:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0011_alter_allcitypopularity_code_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='audiencecities',
            name='tourism_type',
            field=models.CharField(blank=True, choices=[('gastro', 'гастротуризм'), ('museum', 'музейный туризм'), ('spa', 'оздоровительный туризм'), ('beach', 'пляжный туризм'), ('industry', 'промышленный туризм'), ('outdoor', 'развлекательный туризм'), ('pilgrimage', 'религиозный туризм'), ('extreme', 'спортивный туризм'), ('theatre', 'театральный туризм'), ('shopping', 'шопинг-туризм'), ('recreation', 'экологический туризм'), ('excursion', 'экскурсионный туризм')], db_index=True, max_length=10, null=True, verbose_name='Вид туризма'),
        ),
        migrations.AlterField(
            model_name='audienceregions',
            name='tourism_type',
            field=models.CharField(blank=True, choices=[('gastro', 'гастротуризм'), ('museum', 'музейный туризм'), ('spa', 'оздоровительный туризм'), ('beach', 'пляжный туризм'), ('industry', 'промышленный туризм'), ('outdoor', 'развлекательный туризм'), ('pilgrimage', 'религиозный туризм'), ('extreme', 'спортивный туризм'), ('theatre', 'театральный туризм'), ('shopping', 'шопинг-туризм'), ('recreation', 'экологический туризм'), ('excursion', 'экскурсионный туризм')], db_index=True, max_length=10, null=True, verbose_name='Вид туризма'),
        ),
        migrations.AlterField(
            model_name='citycitypopularity',
            name='tourism_type',
            field=models.CharField(blank=True, choices=[('gastro', 'гастротуризм'), ('museum', 'музейный туризм'), ('spa', 'оздоровительный туризм'), ('beach', 'пляжный туризм'), ('industry', 'промышленный туризм'), ('outdoor', 'развлекательный туризм'), ('pilgrimage', 'религиозный туризм'), ('extreme', 'спортивный туризм'), ('theatre', 'театральный туризм'), ('shopping', 'шопинг-туризм'), ('recreation', 'экологический туризм'), ('excursion', 'экскурсионный туризм')], db_index=True, max_length=10, null=True, verbose_name='Вид туризма'),
        ),
        migrations.AlterField(
            model_name='cityrating',
            name='tourism_type',
            field=models.CharField(blank=True, choices=[('gastro', 'гастротуризм'), ('museum', 'музейный туризм'), ('spa', 'оздоровительный туризм'), ('beach', 'пляжный туризм'), ('industry', 'промышленный туризм'), ('outdoor', 'развлекательный туризм'), ('pilgrimage', 'религиозный туризм'), ('extreme', 'спортивный туризм'), ('theatre', 'театральный туризм'), ('shopping', 'шопинг-туризм'), ('recreation', 'экологический туризм'), ('excursion', 'экскурсионный туризм')], db_index=True, max_length=10, null=True, verbose_name='Вид туризма'),
        ),
        migrations.AlterField(
            model_name='cityregionpopularity',
            name='tourism_type',
            field=models.CharField(blank=True, choices=[('gastro', 'гастротуризм'), ('museum', 'музейный туризм'), ('spa', 'оздоровительный туризм'), ('beach', 'пляжный туризм'), ('industry', 'промышленный туризм'), ('outdoor', 'развлекательный туризм'), ('pilgrimage', 'религиозный туризм'), ('extreme', 'спортивный туризм'), ('theatre', 'театральный туризм'), ('shopping', 'шопинг-туризм'), ('recreation', 'экологический туризм'), ('excursion', 'экскурсионный туризм')], db_index=True, max_length=10, null=True, verbose_name='Вид туризма'),
        ),
        migrations.AlterField(
            model_name='regioncitypopularity',
            name='tourism_type',
            field=models.CharField(blank=True, choices=[('gastro', 'гастротуризм'), ('museum', 'музейный туризм'), ('spa', 'оздоровительный туризм'), ('beach', 'пляжный туризм'), ('industry', 'промышленный туризм'), ('outdoor', 'развлекательный туризм'), ('pilgrimage', 'религиозный туризм'), ('extreme', 'спортивный туризм'), ('theatre', 'театральный туризм'), ('shopping', 'шопинг-туризм'), ('recreation', 'экологический туризм'), ('excursion', 'экскурсионный туризм')], db_index=True, max_length=10, null=True, verbose_name='Вид туризма'),
        ),
        migrations.AlterField(
            model_name='regionrating',
            name='tourism_type',
            field=models.CharField(blank=True, choices=[('gastro', 'гастротуризм'), ('museum', 'музейный туризм'), ('spa', 'оздоровительный туризм'), ('beach', 'пляжный туризм'), ('industry', 'промышленный туризм'), ('outdoor', 'развлекательный туризм'), ('pilgrimage', 'религиозный туризм'), ('extreme', 'спортивный туризм'), ('theatre', 'театральный туризм'), ('shopping', 'шопинг-туризм'), ('recreation', 'экологический туризм'), ('excursion', 'экскурсионный туризм')], db_index=True, max_length=10, null=True, verbose_name='Вид туризма'),
        ),
        migrations.AlterField(
            model_name='regionregionpopularity',
            name='tourism_type',
            field=models.CharField(blank=True, choices=[('gastro', 'гастротуризм'), ('museum', 'музейный туризм'), ('spa', 'оздоровительный туризм'), ('beach', 'пляжный туризм'), ('industry', 'промышленный туризм'), ('outdoor', 'развлекательный туризм'), ('pilgrimage', 'религиозный туризм'), ('extreme', 'спортивный туризм'), ('theatre', 'театральный туризм'), ('shopping', 'шопинг-туризм'), ('recreation', 'экологический туризм'), ('excursion', 'экскурсионный туризм')], db_index=True, max_length=10, null=True, verbose_name='Вид туризма'),
        ),
    ]
