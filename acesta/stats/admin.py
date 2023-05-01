import datetime
from itertools import groupby

import environ
from django.contrib import admin
from django.db import models
from django.utils import timezone
from django.views.generic import TemplateView
from Levenshtein import ratio

from acesta.geo.models import Region
from acesta.geo.models import Sight
from acesta.stats.models import AllCityPopularity
from acesta.stats.models import AllRegionPopularity
from acesta.stats.models import AudienceCities
from acesta.stats.models import AudienceRegions
from acesta.stats.models import CityCityPopularity
from acesta.stats.models import CityRating
from acesta.stats.models import CityRegionPopularity
from acesta.stats.models import RegionCityPopularity
from acesta.stats.models import RegionRating
from acesta.stats.models import RegionRegionPopularity
from acesta.stats.models import Salary
from acesta.stats.models import SightRating

env = environ.Env()


@admin.register(AllCityPopularity)
class AllCityPopularityAdmin(admin.ModelAdmin):
    """
    Популярность в городах
    """

    readonly_fields = (
        "sight",
        "home_code",
        "source_code",
        "code",
        "sight_group",
    )
    list_filter = (
        "sight_group",
        "source_code",
    )
    list_display = (
        "sight",
        "home_code",
        "code",
        "qty",
        "popularity_mean",
        "popularity_mean_all",
        "popularity_max",
        "date",
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(CityCityPopularity)
class CityCityPopularityAdmin(admin.ModelAdmin):
    """
    Популярность городов в других городах
    """

    readonly_fields = (
        "home_code",
        "code",
        "tourism_type",
    )
    list_filter = (
        "tourism_type",
        "home_code__code",
    )
    list_display = (
        "home_code",
        "code",
        "qty",
        "popularity_mean",
        "popularity_mean_all",
        "popularity_max",
        "date",
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(RegionCityPopularity)
class RegionCityPopularityAdmin(admin.ModelAdmin):
    """
    Популярность регионов в городах
    """

    readonly_fields = (
        "home_code",
        "code",
        "tourism_type",
    )
    list_filter = (
        "tourism_type",
        "home_code",
    )
    list_display = (
        "home_code",
        "code",
        "qty",
        "popularity_mean",
        "popularity_mean_all",
        "popularity_max",
        "date",
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(CityRegionPopularity)
class CityRegionPopularityAdmin(admin.ModelAdmin):
    """
    Популярность городов в регионах
    """

    readonly_fields = (
        "home_code",
        "code",
        "tourism_type",
    )
    list_filter = (
        "tourism_type",
        "home_code__code",
    )
    list_display = (
        "home_code",
        "code",
        "qty",
        "popularity_mean",
        "popularity_mean_all",
        "popularity_max",
        "date",
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(AllRegionPopularity)
class AllRegionPopularity(admin.ModelAdmin):
    """
    Популярность в регионах
    """

    readonly_fields = (
        "sight",
        "home_code",
        "code",
        "sight_group",
    )
    list_filter = (
        "sight_group",
        "home_code",
    )
    list_display = (
        "sight",
        "home_code",
        "code",
        "qty",
        "popularity_mean",
        "popularity_mean_all",
        "popularity_max",
        "date",
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(RegionRegionPopularity)
class RegionRegionPopularityAdmin(admin.ModelAdmin):
    """
    Популярность регионов в других регионах
    """

    readonly_fields = (
        "home_code",
        "tourism_type",
    )
    list_filter = (
        "tourism_type",
        "home_code",
    )
    list_display = (
        "home_code",
        "code",
        "qty",
        "popularity_mean",
        "popularity_mean_all",
        "popularity_max",
        "date",
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(AudienceCities)
class AudienceCitiesAdmin(admin.ModelAdmin):

    list_filter = (
        "date",
        "tourism_type",
        "code",
    )
    list_display = (
        "tourism_type",
        "code",
        "sex",
        "age",
        "v_all",
        "v_types",
        "v_type_sex_age",
        "modified",
    )

    list_display_links = (
        "tourism_type",
        "code",
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(AudienceRegions)
class AudienceRegionsAdmin(admin.ModelAdmin):

    list_filter = (
        "date",
        "tourism_type",
        "code",
    )
    list_display = (
        "tourism_type",
        "code",
        "sex",
        "age",
        "v_all",
        "v_types",
        "v_type_sex_age",
        "modified",
    )

    list_display_links = (
        "tourism_type",
        "code",
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(CityRating)
class CityRatingAdmin(admin.ModelAdmin):
    """ """

    list_filter = (
        "date",
        "rating_type",
        "home_code__code",
    )
    list_display = (
        "rating_type",
        "home_code",
        "region_code",
        "city_code",
        "place",
        "modified",
    )

    list_display_links = ("home_code",)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(RegionRating)
class RegionRatingAdmin(admin.ModelAdmin):
    """ """

    list_filter = (
        "date",
        "rating_type",
    )
    list_display = (
        "rating_type",
        "home_code",
        "region_code",
        "city_code",
        "place",
        "modified",
    )

    list_display_links = ("home_code",)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(SightRating)
class SightRatingAdmin(admin.ModelAdmin):
    """ """

    list_filter = (
        "date",
        "rating_type",
        "sight__group__tourism_type",
        "sight__code",
    )
    list_display = (
        "rating_type",
        "sight",
        "region_code",
        "city_code",
        "place",
        "modified",
    )

    list_display_links = ("sight",)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Salary)
class SalaryAdmin(admin.ModelAdmin):
    """
    Управление уровнями дохода
    """

    list_filter = (
        "value_type",
        "quarter",
        "year",
        "code",
    )
    list_display = (
        "value_type",
        "code",
        "quarter",
        "year",
        "value",
        "created",
        "modified",
    )

    def has_delete_permission(self, request, obj=None):
        return False


class MonitorAdmin(TemplateView):

    queries_data = []

    @staticmethod
    def sort_monitor(monitor, column) -> dict:
        """
        Sorts monitor dict by column
        :param monitor: dict
        :param column: str
        :return: dict
        """
        return dict(
            sorted(
                monitor.items(),
                key=lambda x: x[1].get(column),
                reverse=True if column != "code" else False,
            )
        )

    def get_sights_monitor(self) -> dict:
        """
        Returns Sights monitor
        :return: dict
        """
        regions_data = {
            r["code"]: {"code": r["code"], "title": r["title"], "qty": r["qty"]}
            for r in Region.objects.all()
            .annotate(qty=models.Count("region_sights"))
            .order_by("code")
            .values("code", "title", "qty")
        }

        not_checked = {
            code: {"not_checked": value}
            for code, value in dict(
                Region.objects.filter(region_sights__is_checked=False)
                .annotate(not_checked=models.Count("region_sights"))
                .values_list("code", "not_checked")
            ).items()
        }
        {
            k: v.update(not_checked.get(k) or {"not_checked": 0})
            for k, v in regions_data.items()
        }

        empty_kernels = {
            code: {"empty_kernels": value}
            for code, value in dict(
                Region.objects.filter(
                    region_sights__kernel=[], region_sights__is_pub=True
                )
                .annotate(empty_kernels=models.Count("region_sights"))
                .values_list("code", "empty_kernels")
            ).items()
        }
        {
            k: v.update(empty_kernels.get(k) or {"empty_kernels": 0})
            for k, v in regions_data.items()
        }

        old_kernels = {
            code: {"old_kernels": value}
            for code, value in dict(
                Region.objects.filter(
                    region_sights__modified_kernel__lt=timezone.now()
                    - datetime.timedelta(days=env.int("KERNEL_PERIOD", default=90)),
                    region_sights__is_pub=True,
                )
                .annotate(old_kernels=models.Count("region_sights"))
                .values_list("code", "old_kernels")
            ).items()
        }
        {
            k: v.update(old_kernels.get(k) or {"old_kernels": 0})
            for k, v in regions_data.items()
        }

        not_in_region = {
            code: {"not_in_region": value}
            for code, value in dict(
                Region.objects.filter(
                    region_sights__is_in_geo_region=False, region_sights__is_pub=True
                )
                .annotate(not_in_region=models.Count("region_sights"))
                .values_list("code", "not_in_region")
            ).items()
        }
        {
            k: v.update(not_in_region.get(k) or {"not_in_region": 0})
            for k, v in regions_data.items()
        }

        empty_titles = {
            code: {"empty_titles": value}
            for code, value in dict(
                Region.objects.filter(
                    region_sights__title__isnull=True, region_sights__is_pub=True
                )
                .annotate(empty_titles=models.Count("region_sights"))
                .values_list("code", "empty_titles")
            ).items()
        }
        {
            k: v.update(empty_titles.get(k) or {"empty_titles": 0})
            for k, v in regions_data.items()
        }

        if self.kwargs.get("sort") and self.kwargs.get("sort").startswith("sights"):
            regions_data = MonitorAdmin.sort_monitor(
                regions_data, self.kwargs.get("sort").replace("sights_", "")
            )
        return regions_data

    def get_ppt_monitor(self) -> dict:
        """
        Returns Popularity monitor
        :return: dict
        """
        regions_data = {
            r["code"]: {"code": r["code"], "title": r["title"]}
            for r in Region.objects.all().order_by("code").values("code", "title")
        }

        wrong_region = {
            code: {"wrong_region": value}
            for code, value in dict(
                Sight.objects.values("code")
                .annotate(qt=models.Count("id"))
                .filter(
                    ~models.Q(sight_all_region_popularity__home_code=models.F("code")),
                    is_checked=True,
                    is_pub=True,
                )
                .exclude(sight_all_region_popularity__home_code__isnull=True)
                .values_list("code", "qt")
            ).items()
        }
        {
            k: v.update(wrong_region.get(k) or {"wrong_region": 0})
            for k, v in regions_data.items()
        }

        no_data = {
            code: {"no_data": value}
            for code, value in dict(
                Sight.objects.values("code")
                .annotate(qt=models.Count("id"))
                .filter(
                    is_checked=True,
                    is_pub=True,
                    sight_all_region_popularity__home_code__isnull=True,
                )
                .values_list("code", "qt")
            ).items()
        }
        {k: v.update(no_data.get(k) or {"no_data": 0}) for k, v in regions_data.items()}

        old_data = {
            code: {"old_data": value}
            for code, value in dict(
                Sight.objects.values("code")
                .annotate(qt=models.Count("id", distinct=True))
                .filter(
                    sight_all_region_popularity__modified__lt=timezone.now()
                    - datetime.timedelta(days=env.int("POPULARITY_PERIOD", default=30))
                )
                .values_list("code", "qt")
            ).items()
        }
        {
            k: v.update(old_data.get(k) or {"old_data": 0})
            for k, v in regions_data.items()
        }

        few_queries = {
            code: {"few_queries": len(list(g))}
            for code, g in groupby(
                filter(
                    lambda x: x[1] and x[2] and x[1] / x[2] < 0.3, self.queries_data
                ),
                key=lambda x: x[0],
            )
        }
        {
            k: v.update(few_queries.get(k) or {"few_queries": 0})
            for k, v in regions_data.items()
        }

        many_queries = {
            code: {"many_queries": len(list(g))}
            for code, g in groupby(
                filter(
                    lambda x: x[1] and x[2] and x[2] / x[1] < 0.3, self.queries_data
                ),
                key=lambda x: x[0],
            )
        }
        {
            k: v.update(many_queries.get(k) or {"many_queries": 0})
            for k, v in regions_data.items()
        }

        if self.kwargs.get("sort") and self.kwargs.get("sort").startswith("ppt"):
            regions_data = MonitorAdmin.sort_monitor(
                regions_data, self.kwargs.get("sort").replace("ppt_", "")
            )

        return regions_data

    def get_audience_monitor(self) -> dict:
        """
        Returns Audience monitor
        :return: dict
        """
        regions_data = {
            r["code"]: {
                "code": r["code"],
                "title": r["code__title"],
                "bad_coeff": 1 if r["mn"] != r["mx"] else 0,
                "coeff": r["mx"],
            }
            for r in AudienceRegions.objects.all()
            .annotate(mn=models.Min("coeff"), mx=models.Max("coeff"))
            .order_by("code")
            .values("code", "code__title", "mn", "mx")
            .distinct()
        }

        no_data_region = {
            code: {"no_data_region": 0 if value else 1}
            for code, value in dict(
                Region.objects.values("code")
                .annotate(qty=models.Count("region_cities__city_audience"))
                .values_list("code", "qty")
            ).items()
        }
        {
            k: v.update(no_data_region.get(k) or {"no_data_region": 0})
            for k, v in regions_data.items()
        }

        no_data_city = {
            code: {"no_data_city": value}
            for code, value in dict(
                Region.objects.values("code")
                .annotate(qty=models.Count("region_cities"))
                .exclude(region_cities__city_audience__isnull=False)
                .values_list("code", "qty")
            ).items()
        }
        {
            k: v.update(no_data_city.get(k) or {"no_data_city": 0})
            for k, v in regions_data.items()
        }

        empty_city = {
            code: {"empty_city": value}
            for code, value in dict(
                AudienceCities.objects.filter(v_all=0)
                .values("code__code", "code__code__title")
                .annotate(qty=models.Count("code", distinct=True))
                .values_list("code__code", "qty")
            ).items()
        }
        {
            k: v.update(empty_city.get(k) or {"empty_city": 0})
            for k, v in regions_data.items()
        }

        bad_coeff_city = {
            code: {"bad_coeff_city": value}
            for code, value in dict(
                AudienceCities.objects.values("code")
                .annotate(
                    mn=models.Min("coeff"),
                    mx=models.Max("coeff"),
                    qty=models.Count("code", distinct=True),
                )
                .exclude(mn=models.F("mx"))
                .values_list("code__code", "qty")
            ).items()
        }
        {
            k: v.update(bad_coeff_city.get(k) or {"bad_coeff_city": 0})
            for k, v in regions_data.items()
        }

        old_data_region = {
            code: {"old_data_region": value}
            for code, value in dict(
                AudienceRegions.objects.filter(
                    modified__lt=timezone.now()
                    - datetime.timedelta(days=env.int("AUDIENCE_PERIOD", default=180)),
                )
                .values_list("code")
                .annotate(old_data=models.Count("code", distinct=True))
                .values_list("code", "old_data")
            ).items()
        }
        {
            k: v.update(old_data_region.get(k) or {"old_data_region": 0})
            for k, v in regions_data.items()
        }

        old_data_cities = {
            code: {"old_data_cities": value}
            for code, value in dict(
                AudienceCities.objects.filter(
                    modified__lt=timezone.now()
                    - datetime.timedelta(days=env.int("AUDIENCE_PERIOD", default=180)),
                )
                .values_list("code__code")
                .annotate(old_data=models.Count("code", distinct=True))
                .values_list("code__code", "old_data")
            ).items()
        }
        {
            k: v.update(old_data_cities.get(k) or {"old_data_cities": 0})
            for k, v in regions_data.items()
        }

        if self.kwargs.get("sort") and self.kwargs.get("sort").startswith("audience"):
            regions_data = MonitorAdmin.sort_monitor(
                regions_data, self.kwargs.get("sort").replace("audience_", "")
            )

        return regions_data

    def get_suspicious_queries(self) -> list:
        """
        Returns Suspicious queries monitor
        :return: list
        """
        suspicious_queries = [
            {
                "code": sight[0],
                "qty": sight[1],
                "kernel": sight[2],
                "title": sight[3],
                "sight_id": sight[4],
                "sight_title": sight[5],
            }
            for sight in self.queries_data
            if (
                sight[1]
                and sight[2]
                and (sight[1] / sight[2] < 0.3 or sight[2] / sight[1] < 0.3)
            )
            or (sight[2] and not sight[1])
        ]

        if self.kwargs.get("sort") and self.kwargs.get("sort").startswith(
            "suspicious_queries"
        ):
            column = self.kwargs.get("sort").replace("suspicious_queries_", "")
            suspicious_queries = sorted(
                suspicious_queries,
                key=lambda x: x.get(column),
                reverse=True if column in ("qty", "kernel") else False,
            )

        return suspicious_queries

    def get_suspicious_kernels(self, threshold=0.5) -> list:
        """
        Returns Suspicious queries monitor
        :param threshold: int
        :return: list
        """
        suspicious_kernels = [
            {
                "code": sight[0],
                "title": sight[3],
                "sight_id": sight[4],
                "query": sight[6],
                "kernel": sight[7][0],
                "ratio": sight[8],
            }
            for sight in self.queries_data
            if sight[8] < threshold
        ]

        if self.kwargs.get("sort") and self.kwargs.get("sort").startswith(
            "suspicious_kernels"
        ):
            column = self.kwargs.get("sort").replace("suspicious_kernels_", "")
            suspicious_kernels = sorted(
                suspicious_kernels,
                key=lambda x: x.get(column),
                reverse=True if column == "ratio" else False,
            )

        return suspicious_kernels

    def get(self, request, *args, **kwargs):
        self.queries_data = [
            (
                sight.get("code"),
                sight.get("qt"),
                sum([v for k, v in sight.get("kernel")[:3]]),
                sight.get("code__title"),
                sight.get("id"),
                sight.get("title"),
                sight.get("query"),
                sight.get("kernel"),
                ratio(sight.get("query"), sight.get("kernel")[0][0])
                if len(sight.get("kernel"))
                else 1,
            )
            for sight in (
                Sight.objects.annotate(
                    qt=models.Sum("sight_all_region_popularity__qty")
                )
                .filter(is_checked=True, is_pub=True)
                .values(
                    "code",
                    "qt",
                    "kernel",
                    "code__title",
                    "id",
                    "title",
                    "query",
                )
            ).order_by("code")
        ]

        context = self.get_context_data(**kwargs)
        context.update(
            dict(
                title="Монитор",
                sights=self.get_sights_monitor(),
                suspicious_kernels=self.get_suspicious_kernels(),
                suspicious_queries=self.get_suspicious_queries(),
                ppt=self.get_ppt_monitor(),
                audience=self.get_audience_monitor(),
            )
        )
        return self.render_to_response(context)
