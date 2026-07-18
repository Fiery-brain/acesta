from datetime import date
from datetime import datetime
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.dateparse import parse_date
from model_utils.models import TimeStampedModel

from acesta.geo.models import City
from acesta.geo.models import Region
from acesta.geo.models import SightGroup


class HistoryMixin(models.Model):
    """
    History mixin
    """

    history_fields = None
    history = models.JSONField(
        "История",
        max_length=2500,
        default=list,
    )

    @staticmethod
    def _normalize_history_date(value):
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            return parse_date(value)
        return None

    @property
    def previous_history_item(self):
        """Return the latest history item from the previous calendar month."""
        current_date = self._normalize_history_date(getattr(self, "modified", None))
        if current_date is None:
            return {}

        previous_month_date = current_date.replace(day=1) - timedelta(days=1)
        previous_month = (previous_month_date.year, previous_month_date.month)
        previous_item = {}
        previous_date = None
        for item in self.history or []:
            item_date = self._normalize_history_date(item.get("date"))
            if item_date is None or (item_date.year, item_date.month) != previous_month:
                continue
            if previous_date is None or item_date > previous_date:
                previous_item = item
                previous_date = item_date
        return previous_item

    def get_previous_history_value(self, key, default=None):
        return self.previous_history_item.get(key, default)

    def add_history(self, snapshot_date=None):
        if self.history_fields is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define history_fields."
            )
        return self._add_history_snapshot(
            self.history_fields,
            snapshot_date=snapshot_date,
        )

    def rollback_previous_month(self, fill_date):
        """Restore live values from history for the month before ``fill_date``.

        History stores the previous live state, not a duplicate of the current
        state. A restored snapshot is therefore removed from history after its
        values become live again. The method only changes the instance; the
        caller chooses the transaction and persistence strategy.
        """

        fill_date = self._normalize_history_date(fill_date)
        if fill_date is None or self.history_fields is None:
            return False
        previous_month_date = fill_date.replace(day=1) - timedelta(days=1)
        previous_month = (previous_month_date.year, previous_month_date.month)
        field_map = (
            self.history_fields
            if isinstance(self.history_fields, dict)
            else {field: field for field in self.history_fields}
        )
        if not field_map:
            return False

        for index, item in enumerate(self.history or []):
            if not isinstance(item, dict):
                continue
            item_date = self._normalize_history_date(item.get("date"))
            if item_date is None or (item_date.year, item_date.month) != previous_month:
                continue
            if any(history_key not in item for history_key in field_map):
                return False
            for history_key, attr_name in field_map.items():
                setattr(self, attr_name, item[history_key])
            if hasattr(self, "date"):
                current_date = getattr(self, "date", None)
                date_field = None
                if hasattr(self, "_meta"):
                    date_field = self._meta.get_field("date")
                if isinstance(current_date, datetime) or isinstance(
                    date_field, models.DateTimeField
                ):
                    restored_date = datetime.combine(item_date, datetime.min.time())
                    if settings.USE_TZ:
                        restored_date = timezone.make_aware(restored_date)
                    self.date = restored_date
                else:
                    self.date = item_date
            if hasattr(self, "modified"):
                restored_modified = datetime.combine(item_date, datetime.min.time())
                if settings.USE_TZ:
                    restored_modified = timezone.make_aware(restored_modified)
                self.modified = restored_modified
            self.history = list(self.history[:index]) + list(self.history[index + 1 :])
            return True
        return False

    def _get_history_snapshot_date(self, snapshot_date=None):
        snapshot_date = snapshot_date or getattr(self, "date", None)
        snapshot_date = snapshot_date or getattr(self, "modified", None)
        snapshot_date = self._normalize_history_date(snapshot_date)
        return snapshot_date or timezone.localdate()

    def _history_without_snapshot_month(self, history, snapshot_date):
        snapshot_month = (snapshot_date.year, snapshot_date.month)
        filtered_history = []
        for item in history or []:
            item_date = self._normalize_history_date(item.get("date"))
            if item_date is None or (item_date.year, item_date.month) != snapshot_month:
                filtered_history.append(item)
        return filtered_history

    @classmethod
    def build_monthly_history_sql(cls, field_map, snapshot_date_sql):
        snapshot_sql = f"COALESCE({snapshot_date_sql}, current_date)"
        fields_sql = [f"'date', {snapshot_sql}"]
        for history_key, db_column_sql in field_map.items():
            fields_sql.append(f"'{history_key}', {db_column_sql}")

        return models.expressions.RawSQL(
            f"""
            jsonb_build_array(
                jsonb_build_object(
                    {", ".join(fields_sql)}
                )
            )
            ||
            COALESCE(
                (
                    SELECT jsonb_agg(history_item)
                    FROM jsonb_array_elements(
                        CASE
                            WHEN jsonb_typeof(history::jsonb) = 'array'
                            THEN history::jsonb
                            ELSE '[]'::jsonb
                        END
                    ) AS history_item
                    WHERE
                        (history_item ->> 'date') !~ '^\\d{{4}}-\\d{{2}}-\\d{{2}}'
                        OR date_trunc(
                            'month',
                            (history_item ->> 'date')::date
                        ) <> date_trunc(
                            'month',
                            {snapshot_sql}
                        )
                ),
                '[]'::jsonb
            )
            """,
            [],
        )

    def _add_history_snapshot(self, fields, snapshot_date=None):
        """
        Add one monthly history snapshot from current instance values.

        История в этих моделях устроена не как журнал всех запусков обновления,
        а как ряд месячных точек для графиков. Поэтому здесь намеренно
        сохраняются старые live-значения перед тем, как updater перезапишет
        запись новыми данными. Текущий месяц после обновления и так виден из
        live-полей объекта, а history нужна как предыдущая точка ряда.

        Дедупликация тоже месячная, а не дневная: обновление может идти
        несколько дней подряд или быть перезапущено после сбоя, но на графике
        должна остаться одна актуальная точка за календарный месяц. Поэтому
        перед вставкой мы удаляем из списка все записи того же месяца.

        Дата snapshot берётся из старой date/modified записи, если она есть,
        чтобы не переносить прошлое состояние в месяц текущей наливки. Если
        старой даты нет, используем текущую дату как последний безопасный
        fallback.

        Новую точку кладём в начало списка, потому что остальной код проекта
        ожидает, что свежая история лежит первой. Метод только меняет
        self.history и не вызывает save(): вызывающий код может сохранить
        объект вместе с остальными изменениями одним запросом.
        """
        snapshot_date = self._get_history_snapshot_date(snapshot_date)

        field_map = (
            {field: field for field in fields}
            if not isinstance(fields, dict)
            else fields
        )
        snapshot = {"date": snapshot_date.isoformat()}
        for history_key, attr_name in field_map.items():
            snapshot[history_key] = getattr(self, attr_name)

        self.history = [snapshot] + self._history_without_snapshot_month(
            self.history,
            snapshot_date,
        )

    class Meta:
        abstract = True


class PopularityHistoryMixin(HistoryMixin):
    """
    History operations for popularity records.
    """

    history_fields = {
        "qty": "qty",
        "mean_all": "popularity_mean_all",
        "mean": "popularity_mean",
        "max": "popularity_max",
    }

    class Meta:
        abstract = True


class RatingHistoryMixin(HistoryMixin):
    """
    History operations for rating records.
    """

    history_fields = ["value", "place"]

    class Meta:
        abstract = True


class AudienceHistoryMixin(HistoryMixin):
    """
    History operations for audience records.
    """

    history_fields = [
        "v_all",
        "v_types",
        "v_type_sex_age",
        "v_sex_age",
        "v_sex_age_child_6",
        "v_sex_age_child_7_12",
        "v_sex_age_parents",
        "v_type_in_pair",
        "coeff",
    ]

    class Meta:
        abstract = True


class StorageMixin(models.Model):
    """
    Storage mixin
    """

    storage = models.JSONField(
        "Временное хранилище",
        max_length=2500,
        default=dict,
    )

    class Meta:
        abstract = True


class Popularity(TimeStampedModel, PopularityHistoryMixin):
    """
    Abstract popularity
    """

    date = models.DateTimeField("Дата", null=True, blank=True)
    qty = models.IntegerField(
        "Показы", default=0, help_text="Среднее число показов в месяц", db_index=True
    )
    popularity_mean_all = models.FloatField(
        "Популярность",
        default=0,
        help_text="Средняя региональная популярность в геообъекте по всем запросам",
    )
    popularity_mean = models.FloatField(
        "Популярность > 100",
        default=0,
        help_text="Средняя региональная популярность в геообъекте только по запросам, вызвавшим интерес",
    )
    popularity_max = models.FloatField(
        "Максимальная популярность",
        default=0,
        help_text="Максимальная региональная популярность в геообъекте",
    )

    class Meta:
        abstract = True


class CityPopularity(Popularity):
    """
    Abstract popularity in cities
    """

    code = models.ForeignKey(
        City,
        verbose_name="Интересант",
        on_delete=models.CASCADE,
        related_name="city_%(class)s",
    )

    class Meta:
        abstract = True


class RegionPopularity(Popularity):
    """
    Abstract popularity in regions
    """

    code = models.ForeignKey(
        Region,
        verbose_name="Интересант",
        on_delete=models.CASCADE,
        related_name="region_%(class)s",
    )

    class Meta:
        abstract = True


class SightGroupMixin(models.Model):
    """
    Sight group mixin
    """

    sight_group = models.ForeignKey(
        SightGroup,
        verbose_name="Вид достопримечательности",
        on_delete=models.DO_NOTHING,
        related_name="group_%(class)s",
        max_length=15,
        blank=True,
        null=True,
        db_index=True,
    )

    class Meta:
        abstract = True


class TourismTypeMixin(models.Model):
    """
    Tourism type mixin
    """

    tourism_type = models.CharField(
        "Вид туризма",
        max_length=10,
        choices=settings.TOURISM_TYPES,
        blank=True,
        null=True,
        db_index=True,
    )

    class Meta:
        abstract = True


class Audience(TimeStampedModel, AudienceHistoryMixin, TourismTypeMixin):
    """
    Abstract audience
    """

    date = models.DateField(auto_now=True)
    code = models.CharField(max_length=20)
    sex = models.CharField("Пол", max_length=1, choices=settings.SEX)
    age = models.CharField("Возраст", max_length=5, choices=settings.AGE)
    v_all = models.IntegerField("Общее число по региону", default=0)
    v_types = models.IntegerField("Общее число заинтересованных в туризме", default=0)
    v_type_sex_age = models.IntegerField(
        "Заинтересованные, разбивка: вид туризма, пол, возраст", default=0
    )
    v_sex_age = models.IntegerField("Число определенного пола и возраста", default=0)
    v_sex_age_child_6 = models.IntegerField(
        "Число определенного пола и возраста с детьми до 6 лет", default=0
    )
    v_sex_age_child_7_12 = models.IntegerField(
        "Число определенного пола и возраста с детьми от 7 до 12 лет", default=0
    )
    v_sex_age_parents = models.IntegerField(
        "Число определенного пола и возраста с родителями", default=0
    )
    v_type_in_pair = models.IntegerField(
        "Число определенного пола и возраста с интересом к виду туризма и в паре",
        default=0,
    )
    coeff = models.FloatField("Восстанавливающий коэффициент", default=1)

    class Meta:
        abstract = True


class Rating(TimeStampedModel, RatingHistoryMixin):
    """
    Abstract rating
    """

    date = models.DateField("Дата", auto_now=True)
    rating_type = models.CharField(
        "Вид рейтинга",
        max_length=10,
        choices=settings.RATING_TYPES,
        default=settings.RATING_TYPE_DEFAULT,
    )
    place = models.IntegerField("Место", default=0)
    region_code = models.ForeignKey(
        Region,
        verbose_name="Регион-интересант",
        on_delete=models.CASCADE,
        related_name="region_%(class)s",
        blank=True,
        null=True,
    )
    city_code = models.ForeignKey(
        City,
        verbose_name="Город-интересант",
        on_delete=models.CASCADE,
        related_name="city_%(class)s",
        blank=True,
        null=True,
    )

    value = models.IntegerField(
        "Значение",
        default=0,
        blank=True,
        null=True,
    )

    @property
    def change(self):
        previous_place = self.get_previous_history_value("place")
        if previous_place is None or self.place is None:
            return None
        return previous_place - self.place

    class Meta:
        abstract = True
