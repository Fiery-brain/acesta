from datetime import date
from pathlib import Path
from types import SimpleNamespace

from dateutil.relativedelta import relativedelta
from django import test
from django.contrib.auth import get_user
from django.db import connection
from django.template import Context
from django.template import Template
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from acesta.geo.models import City
from acesta.geo.models import Region
from acesta.geo.models import Sight
from acesta.geo.models import SightGroup
from acesta.stats.helpers.rating import ensure_current_region_amount_rating_place
from acesta.stats.helpers.rating import get_amount_city_rating_state
from acesta.stats.helpers.rating import get_amount_rating_place
from acesta.stats.helpers.rating import get_amount_rating_state
from acesta.stats.helpers.rating import get_amount_region_rating_state
from acesta.stats.helpers.rating import get_compact_region_rating_rows
from acesta.stats.helpers.rating import get_interest_rating_place
from acesta.stats.helpers.rating import get_interest_sight_rating
from acesta.stats.helpers.rating import get_outside_rating_sight
from acesta.stats.helpers.rating import get_rating_place_change
from acesta.stats.helpers.rating import get_synced_region_rating_places
from acesta.stats.helpers.rating import get_top_sights
from acesta.stats.helpers.sights import get_sight_group_counts
from acesta.stats.helpers.sights import get_strong_tourism_types
from acesta.stats.helpers.sights import get_weak_tourism_types
from acesta.stats.models import RegionRating
from acesta.stats.models import SightRating
from acesta.user.helpers import CredentialsMixin


class StatsTest(CredentialsMixin, test.TestCase):
    def test_responses(self):
        """
        Testing of the stats app
        :return: None
        """
        self.assertEqual(get_user(self.client).is_authenticated, False)

        # dashboard unauthorised
        response = self.client.get(reverse("region"), follow=True)
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertEqual(last_url, "/login/?next=/dashboard/")

        # interest unauthorised
        response = self.client.get(reverse("interest"), follow=True)
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertEqual(last_url, "/login/?next=/interest/")

        # rating unauthorised
        response = self.client.get(reverse("rating"), follow=True)
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertEqual(last_url, "/login/?next=/rating/")

        # rating unauthorised
        response = self.client.get(
            reverse("rating-cities", kwargs={"area": "cities"}), follow=True
        )
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertEqual(last_url, "/login/?next=/rating/cities/")

        # rating unauthorised
        response = self.client.get(
            reverse("rating-sights", kwargs={"area": "sights"}), follow=True
        )
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertEqual(last_url, "/login/?next=/rating/sights/")

        # set-region unauthorised
        response = self.client.get(
            reverse("set_region", kwargs={"code": "02"}), follow=True
        )
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertEqual(last_url, "/login/?next=/set_region/02/")

        self.client.login(**self.credentials)
        self.assertEqual(get_user(self.client).is_authenticated, True)

        # dashboard authorised
        response = self.client.get(reverse("region"))
        self.assertEqual(response.status_code, 200)

        # interest authorised
        response = self.client.get(reverse("interest"))
        self.assertEqual(response.status_code, 200)

        # rating authorised
        response = self.client.get(reverse("rating"))
        self.assertEqual(response.status_code, 200)

        # rating authorised
        response = self.client.get(reverse("rating-cities", kwargs={"area": "cities"}))
        self.assertEqual(response.status_code, 302)

        # rating authorised
        response = self.client.get(reverse("rating-sights", kwargs={"area": "sights"}))
        self.assertEqual(response.status_code, 302)

        # set-region authorised
        response = self.client.get(
            reverse("set_region", kwargs={"code": "02"}), follow=True
        )
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertEqual(last_url, "/dashboard/")


class RegionSightsLoadingTest(CredentialsMixin, test.TestCase):
    def setUp(self):
        super().setUp()
        self.region = Region.objects.get(pk="01")
        self.group = SightGroup.objects.create(
            name="test_sights",
            title="Test sights",
            title_gen="Test sights",
            tourism_type="culture",
            is_pub=True,
        )

    def create_sights(self, amount, prefix="Sight", group=None):
        sights = []
        for index in range(amount):
            sight = Sight.objects.create(
                code=self.region,
                title=f"{prefix} {index:02d}",
                is_pub=True,
            )
            sight.group.add(group or self.group)
            sights.append(sight)
        return sights

    def test_region_renders_only_first_twenty_sights(self):
        self.create_sights(25)
        self.client.login(**self.credentials)

        response = self.client.get(f'{reverse("region")}?group=')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["region_sights"]), 20)
        self.assertTrue(response.context["region_sights_has_more"])
        self.assertEqual(response.content.count(b"<tr data-sight-row"), 20)
        self.assertContains(response, reverse("region_sights_remaining"))
        self.assertContains(response, 'aria-disabled="true" disabled')
        self.assertContains(response, "все разделы&nbsp;(25)")
        self.assertContains(response, "Test sights&nbsp;(25)")

    def test_sight_group_counts_include_only_published_data(self):
        other_group = SightGroup.objects.create(
            name="other_sights",
            title="Other sights",
            title_gen="Other sights",
            tourism_type="culture",
            is_pub=True,
        )
        hidden_group = SightGroup.objects.create(
            name="hidden_sights",
            title="Hidden sights",
            title_gen="Hidden sights",
            tourism_type="culture",
            is_pub=False,
        )
        _, second = self.create_sights(2)
        second.group.add(other_group)
        Sight.objects.create(code=self.region, title="Without group", is_pub=True)
        hidden_group_sight = Sight.objects.create(
            code=self.region, title="Hidden group sight", is_pub=True
        )
        hidden_group_sight.group.add(hidden_group)
        unpublished_sight = Sight.objects.create(
            code=self.region, title="Unpublished sight", is_pub=False
        )
        unpublished_sight.group.add(self.group)

        counts = get_sight_group_counts(code=self.region.code, force_refresh=True)

        self.assertEqual(counts["total"], 4)
        self.assertEqual(counts["groups"], {self.group.pk: 2, other_group.pk: 1})

    def test_sight_group_counts_are_read_from_cache(self):
        self.create_sights(2)
        cached_counts = get_sight_group_counts(
            code=self.region.code, force_refresh=True
        )
        self.create_sights(1, prefix="Added after caching")

        counts = get_sight_group_counts(code=self.region.code)

        self.assertEqual(counts, cached_counts)

    def test_remaining_sights_endpoint_returns_the_complete_remainder(self):
        self.create_sights(25)
        self.client.login(**self.credentials)

        response = self.client.get(reverse("region_sights_remaining"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.count(b"<tr data-sight-row"), 5)
        self.assertNotContains(response, "Sight 19")
        for index in range(20, 25):
            self.assertContains(response, f"Sight {index:02d}")

    def test_remaining_sights_endpoint_respects_group_filter(self):
        other_group = SightGroup.objects.create(
            name="other_sights",
            title="Other sights",
            title_gen="Other sights",
            tourism_type="culture",
            is_pub=True,
        )
        self.create_sights(22, prefix="Selected", group=self.group)
        self.create_sights(22, prefix="Other", group=other_group)
        self.client.login(**self.credentials)

        response = self.client.get(
            reverse("region_sights_remaining"), {"group": self.group.pk}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.count(b"<tr data-sight-row"), 2)
        self.assertContains(response, "Selected 20")
        self.assertContains(response, "Selected 21")
        self.assertNotContains(response, "Other")

    def test_short_sight_list_is_complete_in_initial_response(self):
        self.create_sights(5)
        self.client.login(**self.credentials)

        response = self.client.get(f'{reverse("region")}?group=')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["region_sights_has_more"])
        self.assertEqual(response.content.count(b"<tr data-sight-row"), 5)
        self.assertNotContains(response, reverse("region_sights_remaining"))
        self.assertNotContains(response, 'aria-disabled="true" disabled')

    def test_remaining_sights_endpoint_requires_authentication(self):
        response = self.client.get(reverse("region_sights_remaining"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/?next=", response.url)


class AmountRatingPlaceTest(test.TestCase):
    def setUp(self):
        self.old_date = timezone.now() - relativedelta(months=2)

    def create_region(self, code, _id):
        return Region.objects.create(
            code=code,
            _id=_id,
            federal_district="cf",
            region=f"Region {code}",
            title=f"Region {code}",
            region_type="область",
            is_pub=True,
        )

    def create_city(self, region, _id, title=None):
        return City.objects.create(
            code=region,
            _id=_id,
            title=title or f"City {_id}",
            foundation="1900",
            is_pub=True,
        )

    def create_group(self, name, tourism_type):
        return SightGroup.objects.create(
            name=name,
            title=f"Group {name}",
            title_gen=f"Group {name}",
            tourism_type=tourism_type,
            is_pub=True,
        )

    def create_sights(self, region, amount, created=None, city=None, group=None):
        sights = [
            Sight.objects.create(
                code=region,
                title=f"Sight {region.code}-{index}",
                city=city,
                is_pub=True,
            )
            for index in range(amount)
        ]
        if group is not None:
            for sight in sights:
                sight.group.add(group)
        if created is not None:
            Sight.objects.filter(id__in=[sight.id for sight in sights]).update(
                created=created
            )
        return sights

    def test_amount_rating_change_positive_when_region_rises(self):
        target = self.create_region("01", 1)
        leader = self.create_region("02", 2)
        second = self.create_region("03", 3)

        self.create_sights(target, 1, self.old_date)
        self.create_sights(leader, 4, self.old_date)
        self.create_sights(second, 3, self.old_date)
        self.create_sights(target, 5)

        rating = get_amount_rating_place(code=target.code, force_refresh=True)

        self.assertEqual(rating["place"], 1)
        self.assertEqual(rating["previous_place"], 3)
        self.assertEqual(rating["change"], 2)
        self.assertEqual(rating["qty"], 6)
        self.assertEqual(rating["previous_qty"], 1)

    def test_amount_rating_change_negative_when_region_falls(self):
        target = self.create_region("01", 1)
        second = self.create_region("02", 2)
        third = self.create_region("03", 3)

        self.create_sights(target, 4, self.old_date)
        self.create_sights(second, 3, self.old_date)
        self.create_sights(third, 2, self.old_date)
        self.create_sights(second, 3)
        self.create_sights(third, 4)

        rating = get_amount_rating_place(code=target.code, force_refresh=True)

        self.assertEqual(rating["place"], 3)
        self.assertEqual(rating["previous_place"], 1)
        self.assertEqual(rating["change"], -2)
        self.assertEqual(rating["qty"], 4)
        self.assertEqual(rating["previous_qty"], 4)

    def test_amount_rating_change_zero_when_place_does_not_change(self):
        target = self.create_region("01", 1)
        second = self.create_region("02", 2)

        self.create_sights(target, 3, self.old_date)
        self.create_sights(second, 1, self.old_date)

        rating = get_amount_rating_place(code=target.code, force_refresh=True)

        self.assertEqual(rating["place"], 1)
        self.assertEqual(rating["previous_place"], 1)
        self.assertEqual(rating["change"], 0)
        self.assertEqual(rating["qty"], 3)
        self.assertEqual(rating["previous_qty"], 3)

    def test_amount_rating_change_none_without_previous_place(self):
        target = self.create_region("01", 1)
        old_leader = self.create_region("02", 2)

        self.create_sights(old_leader, 1, self.old_date)
        self.create_sights(target, 3)

        rating = get_amount_rating_place(code=target.code, force_refresh=True)

        self.assertEqual(rating["place"], 1)
        self.assertIsNone(rating["previous_place"])
        self.assertIsNone(rating["change"])
        self.assertEqual(rating["qty"], 3)
        self.assertIsNone(rating["previous_qty"])

    def test_amount_rating_state_contains_current_regions_with_previous_data(self):
        target = self.create_region("01", 1)
        old_leader = self.create_region("02", 2)
        new_region = self.create_region("03", 3)

        self.create_sights(target, 2, self.old_date)
        self.create_sights(old_leader, 3, self.old_date)
        self.create_sights(target, 3)
        self.create_sights(new_region, 1)

        rating_state = get_amount_rating_state(force_refresh=True)

        self.assertEqual(set(rating_state), {"01", "02", "03"})
        self.assertEqual(
            rating_state[target.code],
            {
                "place": 1,
                "qty": 5,
                "previous_place": 2,
                "change": 1,
                "previous_qty": 2,
            },
        )
        self.assertEqual(
            rating_state[new_region.code],
            {
                "place": 3,
                "qty": 1,
                "previous_place": None,
                "change": None,
                "previous_qty": None,
            },
        )

    def test_amount_region_rating_state_uses_tourism_type(self):
        beach = self.create_group("beach_group", "beach")
        outdoor = self.create_group("outdoor_group", "outdoor")
        target = self.create_region("01", 1)
        leader = self.create_region("02", 2)
        outside_tourism_type = self.create_region("03", 3)

        self.create_sights(target, 1, self.old_date, group=beach)
        self.create_sights(leader, 4, self.old_date, group=beach)
        self.create_sights(target, 5, group=beach)
        self.create_sights(outside_tourism_type, 10, self.old_date, group=outdoor)

        rating_state = get_amount_region_rating_state(
            tourism_type="beach",
            force_refresh=True,
        )

        self.assertEqual([rating["code"] for rating in rating_state], ["01", "02"])
        self.assertEqual(
            rating_state[0],
            {
                "code": "01",
                "code__title": "Region 01",
                "qty": 6,
                "place": 1,
                "previous_place": 2,
                "change": 1,
                "previous_qty": 1,
            },
        )
        self.assertEqual(rating_state[1]["change"], -1)

    def test_amount_region_rating_counts_sight_once_for_same_tourism_type(self):
        beach = self.create_group("beach_group", "beach")
        another_beach = self.create_group("another_beach_group", "beach")
        target = self.create_region("01", 1)
        sight = self.create_sights(target, 1, group=beach)[0]
        sight.group.add(another_beach)

        rating_state = get_amount_region_rating_state(
            tourism_type="beach",
            force_refresh=True,
        )

        self.assertEqual(rating_state[0]["qty"], 1)

    def test_amount_region_rating_state_change_zero(self):
        beach = self.create_group("beach_group", "beach")
        target = self.create_region("01", 1)
        second = self.create_region("02", 2)

        self.create_sights(target, 3, self.old_date, group=beach)
        self.create_sights(second, 1, self.old_date, group=beach)

        rating_state = get_amount_region_rating_state(
            tourism_type="beach",
            force_refresh=True,
        )

        self.assertEqual(rating_state[0]["place"], 1)
        self.assertEqual(rating_state[0]["previous_place"], 1)
        self.assertEqual(rating_state[0]["change"], 0)

    def test_amount_region_rating_state_change_none_without_previous_place(self):
        beach = self.create_group("beach_group", "beach")
        target = self.create_region("01", 1)

        self.create_sights(target, 3, group=beach)

        rating_state = get_amount_region_rating_state(
            tourism_type="beach",
            force_refresh=True,
        )

        self.assertEqual(rating_state[0]["place"], 1)
        self.assertIsNone(rating_state[0]["previous_place"])
        self.assertIsNone(rating_state[0]["change"])
        self.assertIsNone(rating_state[0]["previous_qty"])

    def test_amount_city_rating_state_adds_change(self):
        beach = self.create_group("beach_group", "beach")
        region = self.create_region("01", 1)
        target = self.create_city(region, 1, "Target")
        leader = self.create_city(region, 2, "Leader")
        outside_region = self.create_region("02", 2)
        outside_city = self.create_city(outside_region, 3, "Outside")

        self.create_sights(region, 1, self.old_date, city=target, group=beach)
        self.create_sights(region, 4, self.old_date, city=leader, group=beach)
        self.create_sights(region, 5, city=target, group=beach)
        self.create_sights(
            outside_region, 10, self.old_date, city=outside_city, group=beach
        )

        rating_state = get_amount_city_rating_state(
            code=region.code,
            tourism_type="beach",
            force_refresh=True,
        )

        self.assertEqual(
            [rating["city"] for rating in rating_state], [target.id, leader.id]
        )
        self.assertEqual(rating_state[0]["place"], 1)
        self.assertEqual(rating_state[0]["previous_place"], 2)
        self.assertEqual(rating_state[0]["change"], 1)
        self.assertEqual(rating_state[0]["qty"], 6)
        self.assertEqual(rating_state[0]["previous_qty"], 1)
        self.assertEqual(rating_state[1]["change"], -1)

    def test_amount_city_rating_state_change_zero_and_none(self):
        beach = self.create_group("beach_group", "beach")
        region = self.create_region("01", 1)
        stable = self.create_city(region, 1, "Stable")
        new_city = self.create_city(region, 2, "New")

        self.create_sights(region, 3, self.old_date, city=stable, group=beach)
        self.create_sights(region, 1, city=new_city, group=beach)

        rating_state = get_amount_city_rating_state(
            code=region.code,
            tourism_type="beach",
            force_refresh=True,
        )

        self.assertEqual(rating_state[0]["city"], stable.id)
        self.assertEqual(rating_state[0]["change"], 0)
        self.assertEqual(rating_state[1]["city"], new_city.id)
        self.assertIsNone(rating_state[1]["previous_place"])
        self.assertIsNone(rating_state[1]["change"])


class RatingQueryOptimizationTest(test.TestCase):
    def setUp(self):
        self.region = Region.objects.create(
            code="01",
            _id=1,
            federal_district="cf",
            region="Region 01",
            title="Region 01",
            region_type="область",
            is_pub=True,
        )
        self.city = City.objects.create(
            code=self.region,
            _id=1,
            title="City",
            foundation="1900",
            is_pub=True,
        )
        self.group = SightGroup.objects.create(
            name="beach_group",
            title="Beach",
            title_gen="Beach",
            tourism_type="beach",
            is_pub=True,
        )
        self.sight = Sight.objects.create(
            code=self.region,
            city=self.city,
            title="Sight",
            is_pub=True,
        )
        self.sight.group.add(self.group)
        SightRating.objects.create(
            sight=self.sight,
            region_code=self.region,
            sight_group=self.group,
            place=1,
            value=100,
        )

    def _assert_sight_relations_are_loaded(self, rows):
        for row in rows:
            sight = row.sight if hasattr(row, "sight") else row
            str(sight)
            str(sight.code)
            str(sight.city)
            list(sight.group.all())

    def test_interest_sights_have_no_relation_n_plus_one(self):
        queryset = get_interest_sight_rating.__wrapped__(
            {"sight_group": self.group},
            code=self.region.code,
            sight_group=self.group.name,
        )

        with CaptureQueriesContext(connection) as queries:
            rows = list(queryset)
            self._assert_sight_relations_are_loaded(rows)

        self.assertEqual(len(queries), 2)

    def test_top_sights_have_no_relation_n_plus_one(self):
        SightRating.objects.create(
            sight=self.sight,
            sight_group=self.group,
            place=1,
            value=100,
        )

        with CaptureQueriesContext(connection) as queries:
            rows = list(get_top_sights({"sight_group": self.group}))
            self._assert_sight_relations_are_loaded(rows)

        self.assertEqual(len(queries), 2)

    def test_outside_sights_have_no_relation_n_plus_one(self):
        outside = Sight.objects.create(
            code=self.region,
            city=self.city,
            title="Outside",
            is_pub=True,
        )
        outside.group.add(self.group)

        with CaptureQueriesContext(connection) as queries:
            rows = list(
                get_outside_rating_sight(
                    self.region,
                    {"group": self.group},
                )
            )
            self._assert_sight_relations_are_loaded(rows)

        self.assertEqual(rows, [outside])
        self.assertEqual(len(queries), 2)


class RatingViewsTest(CredentialsMixin, test.TestCase):
    def setUp(self):
        super().setUp()
        self.client.login(**self.credentials)
        user = get_user(self.client)
        user.regions.add(user.current_region)
        SightGroup.objects.create(
            name="beach_group",
            title="Beach",
            title_gen="Beach",
            tourism_type="beach",
            is_pub=True,
        )

    def test_rating_tabs_with_default_and_selected_filters(self):
        cases = (
            ("rating", {}, None),
            ("rating", {}, {"tourism_type": "beach"}),
            ("rating-cities", {"area": "cities"}, None),
            (
                "rating-cities",
                {"area": "cities"},
                {"tourism_type": "beach"},
            ),
            ("rating-sights", {"area": "sights"}, None),
            ("rating-sights", {"area": "sights"}, {"group": "beach_group"}),
        )

        for url_name, kwargs, query in cases:
            with self.subTest(url_name=url_name, query=query):
                response = self.client.get(
                    reverse(url_name, kwargs=kwargs),
                    query or {},
                )
                self.assertEqual(response.status_code, 200)


class HistoryMixinTest(test.SimpleTestCase):
    def test_previous_history_item_uses_previous_month(self):
        rating = RegionRating(
            date=date(2026, 6, 28),
            modified=date(2026, 6, 28),
            history=[
                {"date": "2026-06-20", "place": 7},
                {"date": "2026-05-20", "place": 10},
            ],
        )

        self.assertEqual(
            rating.previous_history_item, {"date": "2026-05-20", "place": 10}
        )

    def test_previous_history_item_uses_latest_date_in_previous_month(self):
        rating = RegionRating(
            date=date(2026, 6, 28),
            modified=date(2026, 6, 28),
            history=[
                {"date": "2026-05-10", "place": 12},
                {"date": "2026-05-25", "place": 10},
                {"date": "2026-04-19", "place": 14},
            ],
        )

        self.assertEqual(
            rating.previous_history_item, {"date": "2026-05-25", "place": 10}
        )

    def test_previous_history_item_handles_year_boundary(self):
        rating = RegionRating(
            date=date(2026, 1, 16),
            modified=date(2026, 1, 16),
            history=[
                {"date": "2026-01-10", "place": 7},
                {"date": "2025-12-23", "place": 10},
            ],
        )

        self.assertEqual(
            rating.previous_history_item, {"date": "2025-12-23", "place": 10}
        )

    def test_previous_history_item_uses_modified_when_date_is_stale(self):
        rating = RegionRating(
            date=date(2023, 1, 5),
            modified=date(2026, 2, 16),
            history=[
                {"date": "2026-02-16", "place": 7},
                {"date": "2026-01-20", "place": 10},
            ],
        )

        self.assertEqual(
            rating.previous_history_item, {"date": "2026-01-20", "place": 10}
        )

    def test_previous_history_item_returns_empty_without_exact_previous_month(self):
        rating = RegionRating(
            date=date(2026, 6, 16),
            modified=date(2026, 6, 16),
            history=[
                {"date": "2026-06-10", "place": 7},
                {"date": "2026-04-20", "place": 10},
            ],
        )

        self.assertEqual(rating.previous_history_item, {})

    def test_previous_history_item_returns_empty_dict_without_history(self):
        rating = RegionRating(
            date=date(2026, 2, 16), modified=date(2026, 2, 16), history=[]
        )

        self.assertEqual(rating.previous_history_item, {})

    def test_get_previous_history_value_uses_default(self):
        rating = RegionRating(
            date=date(2026, 2, 16), modified=date(2026, 2, 16), history=[]
        )

        self.assertIsNone(rating.get_previous_history_value("place"))
        self.assertEqual(rating.get_previous_history_value("place", 0), 0)


class InterestRatingPlaceTest(test.TestCase):
    def create_region(self, code, _id):
        return Region.objects.create(
            code=code,
            _id=_id,
            federal_district="cf",
            region=f"Region {code}",
            title=f"Region {code}",
            region_type="область",
            is_pub=True,
        )

    def test_interest_rating_change_from_previous_history_date(self):
        region = self.create_region("01", 1)
        rating_rec = RegionRating.objects.create(
            home_code=region,
            place=7,
            value=245,
            history=[
                {"date": "2026-02-16", "place": 7, "value": 245},
                {"date": "2026-01-20", "place": 10, "value": 231},
                {"date": "2025-12-23", "place": 8, "value": 200},
            ],
        )
        RegionRating.objects.filter(pk=rating_rec.pk).update(
            date=date(2026, 2, 16), modified=date(2026, 2, 16)
        )

        rating = get_interest_rating_place(code=region.code, force_refresh=True)

        self.assertEqual(
            rating,
            {
                "place": 7,
                "previous_place": 10,
                "change": 3,
                "value": 245,
                "previous_value": 231,
            },
        )

    def test_interest_rating_change_none_without_history(self):
        region = self.create_region("01", 1)
        rating_rec = RegionRating.objects.create(
            home_code=region,
            place=7,
            value=245,
            history=[{"date": "2026-02-16", "place": 7, "value": 245}],
        )
        RegionRating.objects.filter(pk=rating_rec.pk).update(
            date=date(2026, 2, 16), modified=date(2026, 2, 16)
        )

        rating = get_interest_rating_place(code=region.code, force_refresh=True)

        self.assertEqual(rating["place"], 7)
        self.assertIsNone(rating["previous_place"])
        self.assertIsNone(rating["change"])
        self.assertEqual(rating["value"], 245)
        self.assertIsNone(rating["previous_value"])

    def test_interest_rating_place_empty_without_rating(self):
        region = self.create_region("01", 1)

        rating = get_interest_rating_place(code=region.code, force_refresh=True)

        self.assertEqual(
            rating,
            {
                "place": None,
                "previous_place": None,
                "change": None,
                "value": None,
                "previous_value": None,
            },
        )

    def test_rating_place_change_positive_when_region_rises(self):
        rating = RegionRating(
            place=7,
            date=date(2026, 2, 16),
            modified=date(2026, 2, 16),
            history=[
                {"date": "2026-02-16", "place": 7},
                {"date": "2026-01-20", "place": 10},
            ],
        )

        self.assertEqual(get_rating_place_change(rating), 3)

    def test_rating_place_change_negative_when_region_falls(self):
        rating = RegionRating(
            place=10,
            date=date(2026, 2, 16),
            modified=date(2026, 2, 16),
            history=[{"date": "2026-01-20", "place": 7}],
        )

        self.assertEqual(get_rating_place_change(rating), -3)

    def test_rating_place_change_zero_when_place_does_not_change(self):
        rating = RegionRating(
            place=7,
            date=date(2026, 2, 16),
            modified=date(2026, 2, 16),
            history=[{"date": "2026-01-20", "place": 7}],
        )

        self.assertEqual(get_rating_place_change(rating), 0)

    def test_rating_place_change_none_without_history(self):
        rating = RegionRating(
            place=7,
            date=date(2026, 2, 16),
            modified=date(2026, 2, 16),
            history=[],
        )

        self.assertIsNone(get_rating_place_change(rating))


class CompactRegionRatingRowsTest(test.SimpleTestCase):
    def get_rows(self, current_code, count=12, compact_places=None):
        places = [
            {"code": f"{index:02}", "place": index, "qty": 100 - index}
            for index in range(1, count + 1)
        ]
        return get_compact_region_rating_rows(
            places,
            current_code,
            lambda place: place["code"],
            compact_places=compact_places,
        )["rows"]

    def get_visible_places(self, rows):
        return [
            row["place"]
            for row in rows
            if row["type"] == "row" and row["is_compact_visible"]
        ]

    def get_gap_count(self, rows):
        return len([row for row in rows if row["type"] == "gap"])

    def get_row_ranks(self, rows):
        return [(row["place"], row["rank"]) for row in rows if row["type"] == "row"]

    def get_row_rank_bounds(self, rows):
        return [
            (row["place"], row["rank"], row["is_rank_start"], row["is_rank_end"])
            for row in rows
            if row["type"] == "row"
        ]

    def test_synced_region_rating_places_small_gap_uses_continuous_range(self):
        compact_places = get_synced_region_rating_places(
            total=89,
            amount_place=85,
            interest_place=81,
        )

        self.assertEqual(
            sorted(compact_places),
            [1, 2, 3, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89],
        )

    def test_synced_region_rating_places_large_gap_uses_two_windows(self):
        compact_places = get_synced_region_rating_places(
            total=89,
            amount_place=46,
            interest_place=12,
        )

        self.assertEqual(
            sorted(compact_places),
            [1, 2, 3, 10, 11, 12, 13, 14, 44, 45, 46, 47, 48, 87, 88, 89],
        )

    def test_synced_region_rating_places_large_gap_keeps_table_tail_by_total(self):
        amount_places = get_synced_region_rating_places(
            total=74,
            amount_place=46,
            interest_place=12,
        )
        interest_places = get_synced_region_rating_places(
            total=89,
            amount_place=46,
            interest_place=12,
        )

        self.assertEqual(
            sorted(amount_places),
            [1, 2, 3, 10, 11, 12, 13, 14, 44, 45, 46, 47, 48, 72, 73, 74],
        )
        self.assertEqual(
            sorted(interest_places),
            [1, 2, 3, 10, 11, 12, 13, 14, 44, 45, 46, 47, 48, 87, 88, 89],
        )

    def test_synced_region_rating_places_keeps_virtual_region_tail(self):
        compact_places = get_synced_region_rating_places(
            total=50,
            amount_place=50,
            interest_place=12,
        )

        self.assertEqual(
            sorted(compact_places),
            [1, 2, 3, 10, 11, 12, 13, 14, 48, 49, 50],
        )

    def test_synced_region_rating_places_when_interest_place_is_worse(self):
        compact_places = get_synced_region_rating_places(
            total=89,
            amount_place=12,
            interest_place=18,
        )

        self.assertEqual(
            sorted(compact_places),
            [1, 2, 3, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 87, 88, 89],
        )

    def test_synced_region_rating_places_near_top(self):
        compact_places = get_synced_region_rating_places(
            total=12,
            amount_place=2,
            interest_place=5,
        )

        self.assertEqual(sorted(compact_places), [1, 2, 3, 4, 5, 6, 7, 10, 11, 12])

    def test_synced_region_rating_places_near_bottom(self):
        compact_places = get_synced_region_rating_places(
            total=12,
            amount_place=10,
            interest_place=12,
        )

        self.assertEqual(sorted(compact_places), [1, 2, 3, 8, 9, 10, 11, 12])

    def test_compact_region_rating_rows_uses_shared_visible_places(self):
        rows = self.get_rows("07", compact_places={1, 2, 3, 6, 7, 8, 11, 12})

        self.assertEqual(self.get_visible_places(rows), [1, 2, 3, 6, 7, 8, 11, 12])
        self.assertEqual(self.get_gap_count(rows), 2)

    def test_compact_region_rating_gap_uses_first_hidden_place(self):
        rows = self.get_rows("07", compact_places={1, 2, 3, 6, 7, 8, 11, 12})
        gaps = [row for row in rows if row["type"] == "gap"]

        self.assertEqual([gap["place"] for gap in gaps], [4, 9])

    def test_compact_region_rating_rows_adds_change(self):
        places = [
            {"code": "01", "place": 1, "previous_place": 2},
            {"code": "02", "place": 2, "previous_place": 1},
        ]
        rows = get_compact_region_rating_rows(
            places,
            "01",
            lambda place: place["code"],
            get_change=lambda place: place["previous_place"] - place["place"],
            compact_places={1, 2},
        )["rows"]

        self.assertEqual(
            [row["change"] for row in rows if row["type"] == "row"],
            [1, -1],
        )

    def test_compact_region_rating_rows_adds_dynamic_ranks(self):
        rows = self.get_rows("07", count=10, compact_places=set(range(1, 11)))

        self.assertEqual(
            self.get_row_ranks(rows),
            [
                (1, 4),
                (2, 4),
                (3, 3),
                (4, 3),
                (5, 2),
                (6, 2),
                (7, 1),
                (8, 1),
                (9, 0),
                (10, 0),
            ],
        )

    def test_compact_region_rating_hidden_rows_keep_dynamic_ranks(self):
        rows = self.get_rows("07", count=20, compact_places={4, 5, 19, 20})

        self.assertEqual(
            self.get_row_ranks(rows)[:5],
            [(1, 4), (2, 4), (3, 4), (4, 4), (5, 3)],
        )

    def test_compact_region_rating_rows_mark_rank_start_and_end(self):
        rows = self.get_rows("07", count=10, compact_places=set(range(1, 11)))

        self.assertEqual(
            self.get_row_rank_bounds(rows),
            [
                (1, 4, True, False),
                (2, 4, False, True),
                (3, 3, True, False),
                (4, 3, False, True),
                (5, 2, True, False),
                (6, 2, False, True),
                (7, 1, True, False),
                (8, 1, False, True),
                (9, 0, True, False),
                (10, 0, False, True),
            ],
        )

    def test_compact_region_rating_single_row_rank_is_start_and_end(self):
        rows = self.get_rows("01", count=1, compact_places={1})
        row = [row for row in rows if row["type"] == "row"][0]

        self.assertTrue(row["is_rank_start"])
        self.assertTrue(row["is_rank_end"])

    def test_compact_region_rating_hidden_rows_keep_rank_bounds(self):
        rows = self.get_rows("07", count=10, compact_places={1, 2, 9, 10})

        self.assertEqual(
            self.get_row_rank_bounds(rows),
            [
                (1, 4, True, False),
                (2, 4, False, True),
                (3, 3, True, False),
                (4, 3, False, True),
                (5, 2, True, False),
                (6, 2, False, True),
                (7, 1, True, False),
                (8, 1, False, True),
                (9, 0, True, False),
                (10, 0, False, True),
            ],
        )

    def test_compact_region_rating_rows_short_list_has_no_gaps_or_hidden_rows(self):
        rows = self.get_rows(
            "03",
            count=5,
            compact_places=get_synced_region_rating_places(
                total=5,
                amount_place=3,
                interest_place=3,
            ),
        )

        self.assertEqual(self.get_visible_places(rows), [1, 2, 3, 4, 5])
        self.assertEqual(self.get_gap_count(rows), 0)
        self.assertFalse(
            any(row["type"] == "row" and not row["is_compact_visible"] for row in rows)
        )

    def test_current_region_is_added_to_amount_rating_when_missing(self):
        current_region = SimpleNamespace(code="03", title="Region 03")
        amount_places = [
            {"code": "01", "code__title": "Region 01", "qty": 3, "place": 1},
            {"code": "02", "code__title": "Region 02", "qty": 1, "place": 2},
        ]

        result = ensure_current_region_amount_rating_place(
            amount_places,
            current_region,
        )

        self.assertEqual(len(result), 3)
        self.assertEqual(
            result[-1],
            {
                "code": "03",
                "code__title": "Region 03",
                "qty": 0,
                "place": 3,
                "previous_place": None,
                "change": None,
                "previous_qty": None,
                "is_virtual": True,
            },
        )

    def test_current_region_is_not_duplicated_in_amount_rating(self):
        current_region = SimpleNamespace(code="02", title="Region 02")
        amount_places = [
            {"code": "01", "code__title": "Region 01", "qty": 3, "place": 1},
            {"code": "02", "code__title": "Region 02", "qty": 1, "place": 2},
        ]

        result = ensure_current_region_amount_rating_place(
            amount_places,
            current_region,
        )

        self.assertEqual(result, amount_places)

    def test_virtual_current_region_is_marked_current_in_compact_rows(self):
        current_region = SimpleNamespace(code="03", title="Region 03")
        amount_places = ensure_current_region_amount_rating_place(
            [
                {"code": "01", "code__title": "Region 01", "qty": 3, "place": 1},
                {"code": "02", "code__title": "Region 02", "qty": 1, "place": 2},
            ],
            current_region,
        )

        rows = get_compact_region_rating_rows(
            amount_places,
            current_region.code,
            lambda place: place["code"],
            compact_places={3},
        )["rows"]
        current_rows = [
            row for row in rows if row["type"] == "row" and row["is_current"]
        ]

        self.assertEqual(len(current_rows), 1)
        self.assertEqual(current_rows[0]["place"], 3)
        self.assertEqual(current_rows[0]["item"]["qty"], 0)


class PlaceChangeTemplateTagTest(test.SimpleTestCase):
    def get_rating_template_loop_block(self, loop_start):
        template_path = (
            Path(__file__).resolve().parents[2] / "templates/dashboard/rating.html"
        )
        template = template_path.read_text()
        return template.split(loop_start, 1)[1].split("{% endfor %}", 1)[0]

    def render_metric_rank(self, tag_args):
        return Template(
            "{% load stats %}{% metric_rank "
            + tag_args
            + " as rank %}{{ rank.rank }}|{{ rank.class_name }}|{{ rank.text }}"
        ).render(Context())

    def test_metric_rank_from_region_rank(self):
        rendered = self.render_metric_rank('metric="rank" rank=4')

        self.assertEqual(rendered, "4|metric metric-rank rank-4|Лидер по потенциалу")

    def test_metric_rank_best_place(self):
        rendered = self.render_metric_rank('metric="sights" place=1 total=100')

        self.assertEqual(rendered, "4|metric metric-sights rank-4|Лидер по потенциалу")

    def test_metric_rank_group_leader_uses_plural_title(self):
        rendered = self.render_metric_rank('metric="sights" rank=4 group=True')

        self.assertEqual(rendered, "4|metric metric-sights rank-4|Лидеры по потенциалу")

    def test_metric_rank_worst_place(self):
        rendered = self.render_metric_rank('metric="interest" place=100 total=100')

        self.assertEqual(rendered, "0|metric metric-interest rank-0|Начальный интерес")

    def test_metric_rank_middle_place(self):
        rendered = self.render_metric_rank('metric="sights" place=50 total=100')

        self.assertEqual(rendered, "2|metric metric-sights rank-2|Средний потенциал")

    def test_metric_rank_ignores_invalid_values(self):
        rendered = self.render_metric_rank('metric="sights" place="" total=100')

        self.assertEqual(rendered, "||")

    def test_rating_template_uses_group_metric_rank(self):
        rating_template = (
            Path(__file__).resolve().parents[2] / "templates/dashboard/rating.html"
        ).read_text()

        self.assertIn('metric="rank" rank=row.rank group=True', rating_template)
        self.assertIn('metric="interest" rank=row.rank group=True', rating_template)

    def test_region_rating_row_renders_league_marker(self):
        rendered = Template(
            "{% load stats %}"
            "{% metric_rank metric='sights' rank=4 group=True as amount_league %}"
            "<tr class='rating-region-extra rating-current-region' data-rating-rank='4'>"
            "<td class='rating-region-league-cell {{ amount_league.metric_class }} {{ amount_league.rank_class }} "
            "rating-region-league-start rating-region-league-end' "
            "data-bs-toggle='tooltip' title='{{ amount_league.text }}'>"
            "<span class='rating-region-league-line'></span>"
            "<span class='rating-region-league-point rating-region-league-point-start'></span>"
            "<span class='rating-region-league-point rating-region-league-point-end'></span></td>"
            "</tr>"
            "{% metric_rank metric='interest' rank=0 as interest_league %}"
            "<td class='rating-region-league-cell {{ interest_league.metric_class }} {{ interest_league.rank_class }} "
            "rating-region-league-start' data-bs-toggle='tooltip' title='{{ interest_league.text }}'>"
            "<span class='rating-region-league-line'></span>"
            "<span class='rating-region-league-point rating-region-league-point-start'></span>"
            "<span class='rating-region-league-point rating-region-league-point-end'></span></td>"
            "<tr class='rating-region-gap'>"
            "<td class='rating-region-gap-league-cell'></td>"
            "<td colspan='3'></td></tr>"
        ).render(Context())

        self.assertIn("rating-region-league-cell metric-sights rank-4", rendered)
        self.assertIn("rating-region-league-cell metric-interest rank-0", rendered)
        self.assertIn("rating-region-league-start", rendered)
        self.assertIn("rating-region-league-end", rendered)
        self.assertIn("rating-region-league-line", rendered)
        self.assertIn("rating-region-league-point-start", rendered)
        self.assertIn("rating-region-league-point-end", rendered)
        self.assertIn("rating-region-gap-league-cell", rendered)
        self.assertIn("colspan='3'", rendered)
        self.assertNotIn("colspan='4'", rendered)
        self.assertIn("rating-region-extra", rendered)
        self.assertIn("rating-current-region", rendered)
        self.assertIn("rating-region-gap", rendered)
        self.assertIn("data-rating-rank='4'", rendered)
        self.assertIn("data-bs-toggle='tooltip' title='Лидеры по потенциалу'", rendered)
        self.assertIn("title='Лидеры по потенциалу'", rendered)
        self.assertNotIn("rating-region-league-dot", rendered)
        self.assertNotIn("rating-region-league-mark", rendered)
        self.assertNotIn("bg_metric", rendered)
        self.assertNotIn("rating-region-rank-cell", rendered)
        self.assertNotIn("data-rating-rank-toggle", rendered)
        self.assertNotIn("rowspan", rendered)

    def render_region_amount_place_cell(
        self,
        qty,
        place,
        amount_zero_count,
        change=0,
        is_virtual=False,
    ):
        return Template(
            "{% load stats %}"
            "{% if row.item.is_virtual or row.item.qty == 0 and amount_zero_count > 1 %}"
            "<div>-</div>"
            "{% else %}"
            "<div{% if row.place <= 3 %} class='{{ row.place|get_medal_class }}'{% endif %}>{{ row.place }}</div>"
            "{% place_change row.change %}"
            "{% endif %}"
        ).render(
            Context(
                {
                    "row": {
                        "item": {"qty": qty, "is_virtual": is_virtual},
                        "place": place,
                        "change": change,
                    },
                    "amount_zero_count": amount_zero_count,
                }
            )
        )

    def render_region_interest_place_cell(
        self,
        value,
        place,
        interest_zero_count,
        change=0,
    ):
        return Template(
            "{% load stats %}"
            "{% if row.item.value == 0 and interest_zero_count > 1 %}"
            "<div>-</div>"
            "{% else %}"
            "<div{% if row.place <= 3 %} class='{{ row.place|get_medal_class }}'{% endif %}>{{ row.place }}</div>"
            "{% place_change row.change %}"
            "{% endif %}"
        ).render(
            Context(
                {
                    "row": {
                        "item": {"value": value},
                        "place": place,
                        "change": change,
                    },
                    "interest_zero_count": interest_zero_count,
                }
            )
        )

    def test_region_amount_virtual_zero_renders_dash_without_change(self):
        rendered = self.render_region_amount_place_cell(
            qty=0,
            place=48,
            amount_zero_count=1,
            is_virtual=True,
        )

        self.assertIn("<div>-</div>", rendered)
        self.assertNotIn("place_change", rendered)
        self.assertNotIn("medal", rendered)

    def test_region_amount_multiple_zero_renders_dash_without_change(self):
        rendered = self.render_region_amount_place_cell(
            qty=0,
            place=48,
            amount_zero_count=2,
        )

        self.assertIn("<div>-</div>", rendered)
        self.assertNotIn("place_change", rendered)
        self.assertNotIn("medal", rendered)

    def test_region_amount_single_real_zero_renders_place(self):
        rendered = self.render_region_amount_place_cell(
            qty=0,
            place=50,
            amount_zero_count=1,
        )

        self.assertIn(">50</div>", rendered)
        self.assertIn("place_change", rendered)

    def test_region_interest_multiple_zero_renders_dash_without_change(self):
        rendered = self.render_region_interest_place_cell(
            value=0,
            place=48,
            interest_zero_count=2,
        )

        self.assertIn("<div>-</div>", rendered)
        self.assertNotIn("place_change", rendered)
        self.assertNotIn("medal", rendered)

    def test_region_interest_single_zero_renders_place(self):
        rendered = self.render_region_interest_place_cell(
            value=0,
            place=50,
            interest_zero_count=1,
        )

        self.assertIn(">50</div>", rendered)
        self.assertIn("place_change", rendered)

    def render_city_interest_place_cell(self, value, place, interest_city_zero_count):
        return Template(
            "{% load stats %}"
            "{% if place.value == 0 and interest_city_zero_count > 1 %}"
            "<div>-</div>"
            "{% else %}"
            "<div{% if place.place <= 3 %} class='{{ place.place|get_medal_class }}'{% endif %}>{{ place.place }}</div>"
            "{% place_change place %}"
            "{% endif %}"
        ).render(
            Context(
                {
                    "place": SimpleNamespace(
                        value=value,
                        place=place,
                        change=0,
                    ),
                    "interest_city_zero_count": interest_city_zero_count,
                }
            )
        )

    def test_city_interest_multiple_zero_renders_dash_without_change(self):
        rendered = self.render_city_interest_place_cell(
            value=0,
            place=8,
            interest_city_zero_count=2,
        )

        self.assertIn("<div>-</div>", rendered)
        self.assertNotIn("place_change", rendered)
        self.assertNotIn("medal", rendered)

    def test_city_interest_single_zero_renders_place(self):
        rendered = self.render_city_interest_place_cell(
            value=0,
            place=8,
            interest_city_zero_count=1,
        )

        self.assertIn(">8</div>", rendered)
        self.assertIn("place_change", rendered)

    def test_city_interest_nonzero_renders_place(self):
        rendered = self.render_city_interest_place_cell(
            value=10,
            place=1,
            interest_city_zero_count=2,
        )

        self.assertIn(">1</div>", rendered)
        self.assertIn("place_change", rendered)
        self.assertIn("medal", rendered)

    def render_sight_interest_place_cell(self, value, place, interest_sight_zero_count):
        return Template(
            "{% load stats %}"
            "{% if place.value == 0 and interest_sight_zero_count > 1 %}"
            "<div>-</div>"
            "{% else %}"
            "<div{% if place.place <= 3 %} class='{{ place.place|get_medal_class }}'{% endif %}>{{ place.place }}</div>"
            "{% place_change place %}"
            "{% endif %}"
        ).render(
            Context(
                {
                    "place": SimpleNamespace(
                        value=value,
                        place=place,
                        change=0,
                    ),
                    "interest_sight_zero_count": interest_sight_zero_count,
                }
            )
        )

    def test_sight_interest_multiple_zero_renders_dash_without_change(self):
        rendered = self.render_sight_interest_place_cell(
            value=0,
            place=86,
            interest_sight_zero_count=2,
        )

        self.assertIn("<div>-</div>", rendered)
        self.assertNotIn("place_change", rendered)
        self.assertNotIn("medal", rendered)

    def test_sight_interest_single_zero_renders_place(self):
        rendered = self.render_sight_interest_place_cell(
            value=0,
            place=86,
            interest_sight_zero_count=1,
        )

        self.assertIn(">86</div>", rendered)
        self.assertIn("place_change", rendered)

    def test_sight_interest_nonzero_renders_place(self):
        rendered = self.render_sight_interest_place_cell(
            value=8,
            place=3,
            interest_sight_zero_count=2,
        )

        self.assertIn(">3</div>", rendered)
        self.assertIn("place_change", rendered)
        self.assertIn("medal", rendered)

    def test_city_zero_count_condition_is_only_in_city_interest_loop(self):
        self.assertIn(
            "interest_city_zero_count",
            self.get_rating_template_loop_block(
                "{% for place in interest_city_places %}"
            ),
        )
        self.assertNotIn(
            "interest_city_zero_count",
            self.get_rating_template_loop_block(
                "{% for place in interest_sight_places %}"
            ),
        )
        self.assertIn(
            "interest_sight_zero_count",
            self.get_rating_template_loop_block(
                "{% for place in interest_sight_places %}"
            ),
        )
        self.assertNotIn(
            "interest_city_zero_count",
            self.get_rating_template_loop_block("{% for place in top_sights %}"),
        )
        self.assertNotIn(
            "interest_sight_zero_count",
            self.get_rating_template_loop_block("{% for place in top_sights %}"),
        )
        self.assertNotIn(
            "interest_city_zero_count",
            self.get_rating_template_loop_block(
                "{% for place in amount_city_places %}"
            ),
        )

    def render_place_change(self, value):
        return Template("{% load stats %}{% place_change value %}").render(
            Context({"value": value})
        )

    def test_place_change_positive(self):
        rendered = self.render_place_change(2)

        self.assertIn("+2", rendered)
        self.assertNotIn("place_change_negative", rendered)
        self.assertNotIn("place_change_neural", rendered)

    def test_place_change_negative(self):
        rendered = self.render_place_change(-2)

        self.assertIn("-2", rendered)
        self.assertIn("place_change_negative", rendered)

    def test_place_change_zero(self):
        rendered = self.render_place_change(0)

        self.assertIn("+0", rendered)
        self.assertIn("place_change_neural", rendered)

    def test_place_change_none(self):
        rendered = self.render_place_change(None)

        self.assertIn("&nbsp;", rendered)
        self.assertIn("place_change_neural", rendered)

    def test_place_change_dict(self):
        rendered = self.render_place_change({"change": 3})

        self.assertIn("+3", rendered)

    def test_place_change_rating_object(self):
        rendered = self.render_place_change(
            RegionRating(
                place=7,
                date=date(2026, 2, 16),
                modified=date(2026, 2, 16),
                history=[{"date": "2026-01-20", "place": 10}],
            )
        )

        self.assertIn("+3", rendered)

    def test_place_change_empty_string(self):
        rendered = self.render_place_change("")

        self.assertIn("&nbsp;", rendered)
        self.assertIn("place_change_neural", rendered)

    def test_place_change_string_zero(self):
        rendered = self.render_place_change("0")

        self.assertIn("+0", rendered)
        self.assertIn("place_change_neural", rendered)

    def test_place_change_string_negative(self):
        rendered = self.render_place_change("-2")

        self.assertIn("-2", rendered)
        self.assertIn("place_change_negative", rendered)

    def test_place_change_empty_string_dict(self):
        rendered = self.render_place_change({"change": ""})

        self.assertIn("&nbsp;", rendered)

    def test_place_change_string_dict(self):
        rendered = self.render_place_change({"change": "3"})

        self.assertIn("+3", rendered)

    def test_place_block_without_change(self):
        rendered = Template(
            "{% load stats %}{% place_block value=1 total=4 desc='test' %}"
        ).render(Context())

        self.assertIn("place_change_neural", rendered)
        self.assertNotIn("metric-sights", rendered)

    def test_place_block_renders_metric_rank(self):
        rendered = Template(
            "{% load stats %}{% place_block value=1 total=100 desc='test' metric='sights' %}"
        ).render(Context())

        self.assertIn("metric metric-sights rank-4", rendered)
        self.assertIn("Лидер по потенциалу", rendered)


@test.override_settings(
    TOURISM_TYPES_OUTSIDE=(
        ("museum", "музейный туризм"),
        ("beach", "пляжный туризм"),
        ("health", "оздоровительный туризм"),
    )
)
class TourismPotentialContextTest(test.SimpleTestCase):
    def test_strong_tourism_types_use_upper_quartile(self):
        stats = [
            {"name": "museum", "title": "музейный туризм", "cnt": 10},
            {"name": "beach", "title": "пляжный туризм", "cnt": 6},
            {"name": "health", "title": "оздоровительный туризм", "cnt": 2},
        ]

        self.assertEqual(get_strong_tourism_types(stats), ["музейный"])

    def test_weak_tourism_types_returns_absent_types(self):
        stats = [
            {"name": "museum", "title": "музейный туризм", "cnt": 10},
        ]

        self.assertEqual(
            get_weak_tourism_types(stats),
            ["пляжный", "оздоровительный"],
        )


class InterestMapBalloonTest(test.TestCase):
    def test_map_height_uses_valid_viewport_value_and_safe_fallback(self):
        from acesta.stats.dash.interest.map import DEFAULT_INTEREST_MAP_HEIGHT
        from acesta.stats.dash.interest.map import get_interest_map_height

        self.assertEqual(get_interest_map_height({"height": 612.4}), 612)
        self.assertEqual(get_interest_map_height({}), DEFAULT_INTEREST_MAP_HEIGHT)
        self.assertEqual(
            get_interest_map_height({"height": "invalid"}),
            DEFAULT_INTEREST_MAP_HEIGHT,
        )
        self.assertEqual(
            get_interest_map_height({"height": 50}),
            DEFAULT_INTEREST_MAP_HEIGHT,
        )

    def test_resize_updates_layout_without_reload_or_height_cookie(self):
        project_root = Path(__file__).resolve().parents[3]
        script = (project_root / "acesta/static/js/dashboard.interest.js").read_text()
        map_module = (project_root / "acesta/stats/dash/interest/map.py").read_text()
        ui_module = (project_root / "acesta/stats/dash/interest/ui.py").read_text()

        self.assertNotIn("location.reload", script)
        self.assertIn('$(window).on("resize"', script)
        self.assertIn("scheduleInterestLayout", script)
        self.assertIn("splitterRatio", script)
        self.assertNotIn('COOKIES.get("innerHeight")', map_module)
        self.assertNotIn('COOKIES.get("innerHeight")', ui_module)

    def test_viewport_reports_card_bottom_as_top_inset(self):
        script = (
            Path(__file__).resolve().parents[2] / "static/js/dashboard.interest.js"
        ).read_text()

        self.assertIn("cardRect.bottom - mapRect.top + 16", script)
        self.assertIn("topInset: Math.round(topInset)", script)

    def test_arrow_direction_placement_order_never_includes_forward_side(self):
        script = (
            Path(__file__).resolve().parents[2] / "static/js/dashboard.interest.js"
        ).read_text()
        placement_function = script.split(
            "function getInterestMapBalloonPlacementOrder", 1
        )[1].split("$(function ()", 1)[0]

        self.assertIn('["right", "top", "bottom"]', placement_function)
        self.assertIn('["left", "top", "bottom"]', placement_function)
        self.assertIn('["bottom", "left", "right"]', placement_function)
        self.assertIn('["top", "left", "right"]', placement_function)

    def test_balloon_projection_tracks_visible_world_copy_and_map_render(self):
        script = (
            Path(__file__).resolve().parents[2] / "static/js/dashboard.interest.js"
        ).read_text()
        styles = (
            Path(__file__).resolve().parents[2] / "static/css/dashboard.css"
        ).read_text()

        self.assertIn("function normalizeInterestMapLongitude", script)
        self.assertIn("normalizedLongitude - 360", script)
        self.assertIn("normalizedLongitude + 360", script)
        self.assertIn('interestMapLibre.on("render"', script)
        self.assertIn('interestMapLibre.on("idle"', script)
        self.assertIn('"--balloon-tail-x"', script)
        self.assertIn('"--balloon-tail-y"', script)
        self.assertIn("var(--balloon-tail-x)", styles)
        self.assertIn("var(--balloon-tail-y)", styles)

    def test_arrow_width_tracks_zoom_without_touching_other_map_layers(self):
        script = (
            Path(__file__).resolve().parents[2] / "static/js/dashboard.interest.js"
        ).read_text()

        self.assertIn("function getInterestMapArrowWidths", script)
        self.assertIn("(referenceZoom - currentZoom) / 3", script)
        self.assertIn('arrowPart !== "shaft" && arrowPart !== "head"', script)
        self.assertIn(
            'map.setPaintProperty(layerId, "line-width", widths.shaft)', script
        )
        self.assertIn("function buildInterestMapArrowGeometry", script)
        self.assertIn("headLength: 18 + zoomOutProgress * 6", script)
        self.assertIn("headWidth: 12 + zoomOutProgress * 6", script)
        self.assertIn("geometry: geometry.shaft", script)
        self.assertIn("geometry: geometry.head", script)
        self.assertIn('interestMapLibre.on("move", updateInterestMapArrows)', script)
        self.assertIn('interestMapLibre.on("render", updateInterestMapArrows)', script)

    def test_arrow_shaft_stops_inside_head_before_the_tip(self):
        script = (
            Path(__file__).resolve().parents[2] / "static/js/dashboard.interest.js"
        ).read_text()

        self.assertIn("var overlap = Math.max(2, dimensions.shaft / 2)", script)
        self.assertIn(
            "var trimDistance = Math.max(0, dimensions.headLength - overlap)",
            script,
        )
        self.assertIn("shaftPoints = projected.slice(0, pointIndex)", script)
        self.assertIn("coordinates: [[tip, left, right, tip]]", script)

    def test_selected_region_balloon_keeps_warning_in_one_metric_block(self):
        from dash import html

        from acesta.stats.dash.interest.map_connections import BalloonContent
        from acesta.stats.dash.interest.map_connections import MapEntity
        from acesta.stats.dash.interest.map_connections import render_map_balloon

        entity = MapEntity(
            kind="regions",
            identifier="64",
            title="Саратовская область",
            anchor=(46.03, 51.53),
            balloon=BalloonContent(
                title="Саратовская область",
                eyebrow="Популярность в регионе",
                details=(["высокая,", html.Br(), "но аудитория ограничена"],),
                tone="low",
            ),
        )
        balloon = render_map_balloon(entity, "source", (53.2, 56.85))
        properties = balloon.to_plotly_json()["props"]

        self.assertEqual(properties["data-target-lon"], 53.2)
        self.assertEqual(properties["data-target-lat"], 56.85)
        self.assertEqual(len(properties["children"]), 3)
        metric = properties["children"][2]
        self.assertEqual(metric.className, "interest-map-balloon__metric")
        self.assertEqual(metric.children[0], "высокая,")
        self.assertEqual(metric.children[1].to_plotly_json()["type"], "Br")
        self.assertEqual(metric.children[2], "но аудитория ограничена")

    def test_selected_region_balloon_supports_every_popularity_label(self):
        from acesta.stats.dash.interest.map import get_popularity_label

        cases = (
            (None, "нет данных"),
            (0, "низкая"),
            (100, "низкая"),
            (101, "средняя"),
            (501, "высокая"),
            (1001, "очень высокая"),
        )
        for popularity, expected in cases:
            with self.subTest(popularity=popularity):
                self.assertEqual(get_popularity_label(popularity), expected)

    def test_audience_label_requires_elevated_popularity_and_small_audience(self):
        from acesta.stats.dash.interest.map import get_audience_label

        cases = (
            (100, 999, ""),
            (101, 999, "но аудитория ограничена"),
            (501, 999, "но аудитория ограничена"),
            (1001, 999, "но аудитория ограничена"),
            (101, 1000, ""),
            (101, None, ""),
            (101, "invalid", ""),
        )
        for popularity, quantity, expected in cases:
            with self.subTest(popularity=popularity, quantity=quantity):
                self.assertEqual(
                    get_audience_label(popularity, quantity),
                    expected,
                )

    def test_popularity_balloon_detail_adds_conditional_comma_and_break(self):
        from acesta.stats.dash.interest.map import get_popularity_balloon_detail

        self.assertEqual(get_popularity_balloon_detail("низкая", ""), "низкая")
        for label in ("средняя", "высокая", "очень высокая"):
            with self.subTest(label=label):
                detail = get_popularity_balloon_detail(
                    label,
                    "но аудитория ограничена",
                )
                self.assertEqual(detail[0], f"{label},")
                self.assertEqual(detail[1].to_plotly_json()["type"], "Br")
                self.assertEqual(detail[2], "но аудитория ограничена")


class PopularityHeatmapTest(test.TestCase):
    def get_heatmap(self, values):
        from pandas import Series

        from acesta.stats.dash.interest.map import get_popularity_heatmap

        return get_popularity_heatmap(Series(values))

    def test_map_data_uses_static_frame_without_popularity_query(self):
        from unittest import mock

        import pandas as pd

        from acesta.stats.dash.helpers import interest as interest_helpers

        regions = pd.DataFrame(
            {"name": ["Регион с нулём", "Регион без записи"]},
            index=["79", "64"],
        )
        with mock.patch.object(interest_helpers, "get_geojson", return_value=regions):
            map_data = interest_helpers.get_map_df("", "79")

        self.assertTrue(pd.isna(map_data.loc["79", "ppt"]))
        self.assertTrue(pd.isna(map_data.loc["64", "ppt"]))
        self.assertEqual(map_data.loc["79", "qty"], 0)
        self.assertEqual(map_data.loc["64", "qty"], 0)

    def test_region_map_uses_visible_table_rows_as_data_source(self):
        import pandas as pd

        from acesta.stats.dash.interest import map as map_module

        map_data = pd.DataFrame(
            {
                "name": ["Регион с нулём", "Регион без строки"],
                "qty": [0, 0],
                "ppt": [0, 0],
            },
            index=["79", "64"],
        )
        table_data = [{"code": "79", "qty": 10, "ppt": 0}]

        aligned = map_module.apply_region_table_popularity(map_data, table_data)
        customdata, _ = map_module.get_region_hover_data(aligned)

        self.assertEqual(customdata[0], ["Регион с нулём", "низкая"])
        self.assertEqual(customdata[1], ["Регион без строки", "нет данных"])
        self.assertTrue(pd.isna(aligned.loc["64", "ppt"]))

    def test_external_region_colors_keep_their_own_scale(self):
        colors, color_range, _ = self.get_heatmap([706, 271])

        self.assertEqual(color_range, (0, 2))
        self.assertEqual(colors.iloc[0], 2)
        self.assertGreater(colors.iloc[0], colors.iloc[1])
        self.assertGreater(colors.iloc[1], 1)

    def test_home_region_outline_is_background_only_in_point_modes(self):
        from django.conf import settings

        from acesta.stats.dash.interest.map import get_home_region_outline_layers

        source = {"type": "FeatureCollection", "features": []}
        region_layers = get_home_region_outline_layers(source, settings.AREA_REGIONS)
        self.assertEqual(
            [layer["opacity"] for layer in region_layers],
            [0.14, 0.72],
        )
        self.assertTrue(all("below" not in layer for layer in region_layers))

        for home_area in (settings.AREA_CITIES, settings.AREA_SIGHTS):
            with self.subTest(home_area=home_area):
                point_layers = get_home_region_outline_layers(source, home_area)
                self.assertEqual(
                    [layer["opacity"] for layer in point_layers],
                    [0.04, 0.28],
                )
                self.assertTrue(
                    all(layer["below"] == "traces" for layer in point_layers)
                )

    def test_external_heatmap_is_neutral_without_increased_interest(self):
        colors, color_range, color_scale = self.get_heatmap([80, 25])

        self.assertEqual(colors.tolist(), [0, 0])
        self.assertEqual(color_range, (0, 1))
        self.assertEqual(color_scale, ["#eef5f7", "#eef5f7"])

    def test_external_heatmap_distinguishes_missing_from_low_interest(self):
        colors, color_range, color_scale = self.get_heatmap([float("nan"), 0, 100])

        self.assertEqual(colors.tolist(), [-1, 0, 0])
        self.assertEqual(color_range, (-1, 0))
        self.assertEqual(color_scale[0][1], "#ffffff")
        self.assertEqual(color_scale[-1][1], "#eef5f7")

    def test_external_heatmap_keeps_gradient_with_missing_regions(self):
        colors, color_range, color_scale = self.get_heatmap(
            [float("nan"), 100, 101, 501]
        )

        self.assertEqual(colors.iloc[0], -1)
        self.assertEqual(colors.iloc[1], 0)
        self.assertGreater(colors.iloc[2], 1)
        self.assertEqual(colors.iloc[3], 2)
        self.assertEqual(color_range, (-1, 2))
        self.assertEqual(color_scale[0][1], "#ffffff")
        self.assertEqual(color_scale[2][1], "#eef5f7")
        self.assertEqual(color_scale[-1][1], "#90C2BB")

    def test_external_outlier_is_limited_by_percentile(self):
        colors, _, _ = self.get_heatmap([2000, 300, 150])

        self.assertEqual(colors.iloc[0], 2)
        self.assertGreater(colors.iloc[1], colors.iloc[2])

    def test_home_region_layer_has_fixed_color_and_click_context(self):
        import geopandas as gpd
        import plotly.graph_objects as go
        from shapely.geometry import Polygon

        from acesta.stats.dash.interest import map as map_module

        home_region = gpd.GeoDataFrame(
            {
                "name": ["Еврейская автономная область"],
                "qty": [999],
                "ppt": [150],
                "qty_str": ["19 276"],
                "ppt_str": ["36 737"],
                "geometry": [Polygon([(131, 47), (133, 47), (133, 49), (131, 49)])],
            },
            index=["79"],
            crs="EPSG:4326",
        )
        figure = go.Figure()

        map_module.add_home_region_layer(figure, home_region)

        trace = figure.data[0]
        self.assertEqual(trace.type, "choroplethmap")
        self.assertEqual(trace.locations[0], "79")
        self.assertEqual(trace.customdata[0][0], "Еврейская автономная область")
        self.assertEqual(
            trace.customdata[0][1],
            "средняя,<br>но аудитория ограничена",
        )
        self.assertEqual(trace.colorscale[0][1], map_module.HOME_REGION_FILL_COLOR)
        self.assertEqual(trace.colorscale[-1][1], map_module.HOME_REGION_FILL_COLOR)
        self.assertIn("Популярность в регионе", trace.hovertemplate)
        self.assertIn("%{customdata[1]}", trace.hovertemplate)
        self.assertEqual(list(trace.hoverlabel.bgcolor), ["#76bdb0"])
        self.assertEqual(list(trace.hoverlabel.font.color), ["#ffffff"])
        self.assertEqual(trace.hoverlabel.bordercolor, "#ffffff")

    def test_map_excludes_home_region_from_statistical_trace(self):
        import math
        from types import SimpleNamespace
        from unittest import mock

        import geopandas as gpd
        from django.conf import settings
        from shapely.geometry import Polygon

        from acesta.stats.dash.interest import map as map_module

        map_data = gpd.GeoDataFrame(
            {
                "name": ["Еврейская автономная область", "Хабаровский край"],
                "qty": [19276, 999],
                "ppt": [36737, 600],
                "geometry": [
                    Polygon([(131, 47), (133, 47), (133, 49), (131, 49)]),
                    Polygon([(134, 48), (136, 48), (136, 50), (134, 50)]),
                ],
            },
            index=["79", "27"],
            crs="EPSG:4326",
        )
        current_region = SimpleNamespace(
            code="79",
            title="Еврейская автономная область",
            rank=2,
            center_lat=48.5,
            center_lon=132,
            zoom_regions=4,
            zoom_cities=6,
            get_federal_district_display=lambda: "Дальневосточный",
            get_rank_display=lambda: "Средний",
        )
        user = SimpleNamespace(current_region=current_region, is_extended=True)
        request = SimpleNamespace(COOKIES={"innerHeight": "768"}, user=user)
        table_data = [
            {"code": "79", "qty": 19276, "ppt": 367.37},
            {"code": "27", "qty": 999, "ppt": 6},
        ]
        table_state = {
            "homeArea": settings.AREA_REGIONS,
            "interesantArea": settings.AREA_REGIONS,
            "tourismType": "",
            "targetKey": "regions_0",
            "mapContextKey": "79|regions|regions||regions_0",
            "sourceRowId": None,
        }

        with mock.patch.object(map_module, "get_map_df", return_value=map_data):
            figure, _, _ = map_module.update_map(
                table_state,
                None,
                "",
                settings.AREA_REGIONS,
                settings.AREA_REGIONS,
                "regions_0",
                {"width": 700, "height": 500},
                table_data,
                user=user,
                request=request,
            )

        statistical_trace, home_trace = figure.data
        home_position = list(statistical_trace.locations).index("79")
        external_position = list(statistical_trace.locations).index("27")
        self.assertTrue(math.isnan(statistical_trace.z[home_position]))
        self.assertEqual(
            list(statistical_trace.customdata[external_position]),
            ["Хабаровский край", "высокая,<br>но аудитория ограничена"],
        )
        self.assertEqual(
            statistical_trace.hoverlabel.bgcolor[external_position], "#7cbbb0"
        )
        self.assertEqual(
            statistical_trace.hoverlabel.font.color[external_position], "#ffffff"
        )
        self.assertIn("Популярность в регионе", statistical_trace.hovertemplate)
        self.assertEqual(home_trace.locations[0], "79")
        self.assertEqual(home_trace.colorscale[0][1], map_module.HOME_REGION_FILL_COLOR)

    def test_country_background_includes_every_configured_new_region(self):
        from acesta.stats.dash.helpers.interest import get_geojson
        from acesta.stats.dash.interest.map import get_country_background_layers

        map_data = get_geojson()
        expected_codes = {"81", "82", "84", "85", "91", "92"}

        self.assertTrue(expected_codes.issubset(set(map_data.index.astype(str))))
        layers = get_country_background_layers(map_data)
        self.assertEqual(layers[0]["source"]["type"], "Feature")
        self.assertEqual(layers[1]["source"]["type"], "Feature")
        self.assertEqual(
            layers[0]["source"]["geometry"], layers[1]["source"]["geometry"]
        )

    def test_country_background_accepts_point_mode_style(self):
        import geopandas as gpd
        from shapely.geometry import Polygon

        from acesta.stats.dash.interest.map import get_country_background_layers

        map_data = gpd.GeoDataFrame(
            {"geometry": [Polygon([(30, 50), (32, 50), (32, 52), (30, 52)])]},
            index=["79"],
            crs="EPSG:4326",
        )

        fill, line = get_country_background_layers(
            map_data,
            fill_color="#dbfffa",
            opacity=0.45,
            line_color="#000000",
            line_width=0.5,
        )

        self.assertEqual(fill["color"], "#dbfffa")
        self.assertEqual(fill["opacity"], 0.45)
        self.assertEqual(fill["below"], "traces")
        self.assertEqual(line["color"], "#000000")
        self.assertEqual(line["opacity"], 0.45)
        self.assertEqual(line["line"]["width"], 0.5)
        self.assertEqual(line["below"], "traces")

    def test_city_source_point_modes_use_inactive_region_background(self):
        from types import SimpleNamespace
        from unittest import mock

        import geopandas as gpd
        from django.conf import settings
        from shapely.geometry import Polygon

        from acesta.stats.dash.interest import map as map_module

        map_data = gpd.GeoDataFrame(
            {
                "name": ["Домашний регион", "Соседний регион"],
                "qty": [100, 50],
                "ppt": [150, 80],
                "geometry": [
                    Polygon([(30, 50), (32, 50), (32, 52), (30, 52)]),
                    Polygon([(32, 50), (34, 50), (34, 52), (32, 52)]),
                ],
            },
            index=["79", "27"],
            crs="EPSG:4326",
        )
        current_region = SimpleNamespace(
            code="79",
            title="Домашний регион",
            rank=2,
            center_lat=51,
            center_lon=31,
            zoom_regions=4,
            zoom_cities=6,
            get_federal_district_display=lambda: "Тестовый",
            get_rank_display=lambda: "Средний",
        )
        user = SimpleNamespace(current_region=current_region, is_extended=True)
        request = SimpleNamespace(COOKIES={"innerHeight": "768"}, user=user)

        with mock.patch.object(map_module, "get_map_df", return_value=map_data):
            with mock.patch.object(map_module, "get_cities", return_value=[]):
                with mock.patch.object(map_module, "get_sights", return_value=[]):
                    for home_area in (settings.AREA_CITIES, settings.AREA_SIGHTS):
                        with self.subTest(home_area=home_area):
                            target_key = f"{home_area}_0"
                            table_state = {
                                "homeArea": home_area,
                                "interesantArea": settings.AREA_CITIES,
                                "tourismType": "",
                                "targetKey": target_key,
                                "mapContextKey": (
                                    f"79|{home_area}|cities||{target_key}"
                                ),
                                "sourceRowId": None,
                            }
                            with mock.patch.object(
                                map_module,
                                "resolve_target_key",
                                return_value=target_key,
                            ):
                                figure, _, _ = map_module.update_map(
                                    table_state,
                                    None,
                                    "",
                                    home_area,
                                    settings.AREA_CITIES,
                                    target_key,
                                    {"width": 900, "height": 600},
                                    [],
                                    user=user,
                                    request=request,
                                )

                            self.assertEqual(figure.layout.map.style, "open-street-map")
                            background = figure.data[0]
                            self.assertEqual(background.type, "choroplethmap")
                            self.assertEqual(background.marker.opacity, 0.45)
                            self.assertEqual(background.marker.line.color, "#000000")
                            self.assertEqual(background.marker.line.width, 0.5)

                    target_key = f"{settings.AREA_CITIES}_0"
                    with mock.patch.object(
                        map_module,
                        "resolve_target_key",
                        return_value=target_key,
                    ):
                        figure, _, _ = map_module.update_map(
                            {
                                "homeArea": settings.AREA_CITIES,
                                "interesantArea": settings.AREA_REGIONS,
                                "tourismType": "",
                                "targetKey": target_key,
                                "mapContextKey": (f"79|cities|regions||{target_key}"),
                                "sourceRowId": None,
                            },
                            None,
                            "",
                            settings.AREA_CITIES,
                            settings.AREA_REGIONS,
                            target_key,
                            {"width": 900, "height": 600},
                            [],
                            user=user,
                            request=request,
                        )

        self.assertIn("choroplethmap", [trace.type for trace in figure.data])
        self.assertEqual(len(figure.layout.map.layers), 0)

    def test_city_heatmap_coordinates_use_one_bulk_query(self):
        from types import SimpleNamespace
        from unittest import mock

        from acesta.stats.dash.interest import map as map_module

        rows = [
            {"code": "101", "qty": 10, "ppt": 1},
            {"code": "102", "qty": 20, "ppt": 1.01},
            {"code": "103", "qty": 30, "ppt": 5},
        ]
        queryset = mock.Mock()
        queryset.in_bulk.return_value = {
            101: SimpleNamespace(pk=101),
            102: SimpleNamespace(pk=102),
        }
        selected_queryset = mock.Mock()
        selected_queryset.only.return_value = queryset
        with mock.patch.object(
            map_module.City.objects,
            "select_related",
            return_value=selected_queryset,
        ) as select_related:
            items = map_module.get_city_heatmap_items(rows)

        select_related.assert_called_once_with("code")
        selected_queryset.only.assert_called_once_with(
            "id", "title", "lat", "lon", "code__title"
        )
        queryset.in_bulk.assert_called_once()
        self.assertEqual([city.pk for city, _ in items], [101, 102])

    def test_region_from_cities_uses_colored_city_points_without_choropleth(self):
        from types import SimpleNamespace
        from unittest import mock

        import geopandas as gpd
        from django.conf import settings
        from shapely.geometry import Polygon

        from acesta.stats.dash.interest import map as map_module

        map_data = gpd.GeoDataFrame(
            {
                "name": ["Домашний регион", "Соседний регион"],
                "qty": [100, 50],
                "ppt": [150, 80],
                "geometry": [
                    Polygon([(30, 50), (32, 50), (32, 52), (30, 52)]),
                    Polygon([(32, 50), (34, 50), (34, 52), (32, 52)]),
                ],
            },
            index=["79", "27"],
            crs="EPSG:4326",
        )
        rows = [
            {
                "id": str(index),
                "code": str(index),
                "code__title": f"Город {index}",
                "qty": quantity,
                "ppt": popularity / 100,
            }
            for index, quantity, popularity in (
                (101, 10, 100),
                (102, 20, 101),
                (103, 30, 501),
                (104, 40, 1100),
            )
        ]
        cities = [
            SimpleNamespace(
                pk=int(row["code"]),
                id=int(row["code"]),
                title=row["code__title"],
                lon=30 + index,
                lat=51,
                code=SimpleNamespace(title=f"Регион {index}"),
            )
            for index, row in enumerate(rows)
        ]
        current_region = SimpleNamespace(
            code="79",
            title="Домашний регион",
            rank=2,
            center_lat=51,
            center_lon=31,
            zoom_regions=4,
            zoom_cities=6,
            get_federal_district_display=lambda: "Тестовый",
            get_rank_display=lambda: "Средний",
        )
        user = SimpleNamespace(current_region=current_region, is_extended=True)
        request = SimpleNamespace(COOKIES={"innerHeight": "768"}, user=user)

        with mock.patch.object(map_module, "get_map_df", return_value=map_data):
            with mock.patch.object(
                map_module,
                "get_city_heatmap_items",
                return_value=list(zip(cities, rows)),
            ):
                figure, _, balloons = map_module.update_map(
                    {
                        "homeArea": settings.AREA_REGIONS,
                        "interesantArea": settings.AREA_CITIES,
                        "tourismType": "",
                        "targetKey": "regions_0",
                        "mapContextKey": "79|regions|cities||regions_0",
                        "sourceRowId": "101",
                    },
                    {"row": 0, "row_id": "101"},
                    "",
                    settings.AREA_REGIONS,
                    settings.AREA_CITIES,
                    "regions_0",
                    {"width": 900, "height": 600},
                    rows,
                    user=user,
                    request=request,
                )

        self.assertEqual(figure.data[0].type, "choroplethmap")
        city_trace = next(trace for trace in figure.data if trace.type == "scattermap")
        self.assertEqual(
            list(city_trace.ids),
            [f"source-cities_{city.pk}" for city in cities],
        )
        self.assertEqual(
            list(city_trace.marker.color),
            ["#B8C4C8", "#9CCCC8", "#79ADA6", "#4F9286"],
        )
        self.assertEqual(
            list(city_trace.marker.size),
            list(map_module.get_sizes([10, 20, 30, 40])),
        )
        self.assertEqual(city_trace.marker.opacity, 1)
        self.assertEqual(
            list(city_trace.customdata[0]),
            ["Регион 0", "популярность низкая"],
        )
        self.assertEqual(
            list(city_trace.customdata[1]),
            [
                "Регион 1",
                "популярность средняя,<br>но аудитория ограничена",
            ],
        )
        self.assertIn(
            '<span style="font-size: 11px">%{customdata[0]}</span>',
            city_trace.hovertemplate,
        )
        self.assertNotIn("Популярность:", city_trace.hovertemplate)
        self.assertNotIn("%", str(city_trace.customdata))
        self.assertEqual(
            list(city_trace.hoverlabel.bgcolor),
            ["#fefefe", "#76bdb0", "#7cbbb0", "#74b8ac"],
        )
        self.assertEqual(
            list(city_trace.hoverlabel.font.color),
            ["#5f6871", "#ffffff", "#ffffff", "#ffffff"],
        )
        self.assertEqual(city_trace.hoverlabel.bordercolor, "#ffffff")
        balloon_children = balloons[0].to_plotly_json()["props"]["children"]
        self.assertEqual(
            [child.children for child in balloon_children],
            ["Популярность в городе", "Город 101", "низкая"],
        )
        self.assertEqual(figure.layout.map.style, "white-bg")
        self.assertEqual(figure.layout.map.layers[0].type, "circle")
        self.assertIn("line", [layer.type for layer in figure.layout.map.layers])


class MapConnectionEngineTest(test.TestCase):
    def setUp(self):
        from shapely.geometry import Polygon

        from acesta.stats.dash.interest.map_connections import BalloonContent
        from acesta.stats.dash.interest.map_connections import create_point_entity
        from acesta.stats.dash.interest.map_connections import create_region_entity

        self.region_source = create_region_entity(
            "27",
            "Хабаровский край",
            Polygon([(134, 48), (136, 48), (136, 50), (134, 50)]),
            BalloonContent(
                title="Хабаровский край",
                eyebrow="Популярность в регионе",
                details=("очень высокая",),
            ),
        )
        self.region_target = create_region_entity(
            "79",
            "Еврейская автономная область",
            Polygon([(131, 47), (133, 47), (133, 49), (131, 49)]),
        )
        self.city_source = create_point_entity(
            "cities",
            "101",
            "Хабаровск",
            135.07,
            48.48,
            BalloonContent(
                title="Хабаровск",
                eyebrow="Популярность в городе",
                details=("высокая",),
            ),
        )
        self.city_target = create_point_entity(
            "cities",
            "201",
            "Биробиджан",
            132.92,
            48.79,
            BalloonContent(title="Биробиджан"),
        )
        self.sight_target = create_point_entity(
            "sights",
            "301",
            "Набережная",
            132.91,
            48.80,
            BalloonContent(
                title="Набережная",
                eyebrow="городские пространства",
                details=("ул. Набережная",),
            ),
        )

    def build_overlay(self, source, target, right_inset=0, top_inset=0):
        from acesta.stats.dash.interest.map_connections import build_connection_overlay
        from acesta.stats.dash.interest.map_connections import MapConnection

        return build_connection_overlay(
            [MapConnection(source, target)],
            {
                "width": 900,
                "height": 600,
                "rightInset": right_inset,
                "topInset": top_inset,
            },
            600,
            {"lon": 132, "lat": 49},
            4,
            [target] if target.kind != "regions" else [],
        )

    def test_all_six_source_target_combinations_build_one_connection(self):
        sources = (self.region_source, self.city_source)
        targets = (self.region_target, self.city_target, self.sight_target)

        for source in sources:
            for target in targets:
                with self.subTest(source=source.kind, target=target.kind):
                    overlay = self.build_overlay(source, target)

                    expected_layers = 3 if source.kind == "regions" else 4
                    self.assertEqual(len(overlay.layers), expected_layers)
                    expected_balloons = 1 if target.kind == "regions" else 2
                    self.assertEqual(len(overlay.balloons), expected_balloons)
                    self.assertGreater(overlay.zoom, 0)

    def test_coincident_points_have_balloons_but_no_arrow_layers(self):
        from acesta.stats.dash.interest.map_connections import create_point_entity

        target = create_point_entity(
            "sights",
            "401",
            "Центральная площадь",
            self.city_source.anchor[0],
            self.city_source.anchor[1],
            self.sight_target.balloon,
        )

        overlay = self.build_overlay(self.city_source, target)

        self.assertEqual(len(overlay.layers), 2)
        self.assertEqual(len(overlay.balloons), 2)

    def test_same_entity_uses_one_combined_balloon(self):
        overlay = self.build_overlay(self.city_source, self.city_source)
        repeated = self.build_overlay(self.city_source, self.city_source)

        self.assertEqual(len(overlay.layers), 2)
        self.assertEqual(len(overlay.balloons), 1)
        self.assertEqual(overlay.center, repeated.center)
        self.assertEqual(overlay.zoom, repeated.zoom)
        self.assertEqual(
            overlay.balloons[0].to_plotly_json()["props"]["data-role"],
            "self",
        )

    def test_multiple_connections_share_one_renderer(self):
        from acesta.stats.dash.interest.map_connections import build_connection_overlay
        from acesta.stats.dash.interest.map_connections import MapConnection

        overlay = build_connection_overlay(
            [
                MapConnection(self.region_source, self.city_target),
                MapConnection(self.city_source, self.sight_target),
            ],
            {"width": 900, "height": 600},
            600,
            {"lon": 132, "lat": 49},
            4,
            [self.city_target, self.sight_target],
        )

        self.assertEqual(len(overlay.layers), 7)
        self.assertEqual(len(overlay.balloons), 4)

    def test_arrow_uses_one_solid_shaft_without_shadow_or_dash_points(self):
        from acesta.stats.dash.interest.map_connections import ARROW_COLOR
        from acesta.stats.dash.interest.map_connections import build_arrow_curve
        from acesta.stats.dash.interest.map_connections import build_arrow_geometry
        from acesta.stats.dash.interest.map_connections import _build_arrow_layers

        arrow = build_arrow_geometry(
            build_arrow_curve(self.city_source.anchor, self.city_target.anchor),
            zoom=6,
        )
        layers = _build_arrow_layers(arrow)

        self.assertEqual(len(layers), 2)
        self.assertEqual(layers[0]["source"]["geometry"]["type"], "LineString")
        self.assertEqual(layers[0]["line"]["width"], 4)
        self.assertEqual(layers[1]["source"]["geometry"]["type"], "Polygon")
        self.assertEqual(layers[1]["type"], "fill")
        self.assertEqual(
            layers[1]["source"]["geometry"]["coordinates"][0][0],
            layers[1]["source"]["geometry"]["coordinates"][0][-1],
        )
        self.assertEqual(
            layers[0]["source"]["properties"],
            {"acestaArrowPart": "shaft", "acestaArrowZoom": 6},
        )
        self.assertEqual(layers[1]["source"]["properties"]["acestaArrowPart"], "head")
        self.assertEqual(layers[1]["source"]["properties"]["acestaArrowZoom"], 6)
        self.assertEqual(
            layers[1]["source"]["properties"]["acestaArrowPrevious"],
            arrow.curve[-2],
        )
        self.assertEqual(
            layers[1]["source"]["properties"]["acestaArrowEnd"], arrow.curve[-1]
        )
        self.assertTrue(all(layer["color"] == ARROW_COLOR for layer in layers))
        self.assertFalse(
            any(layer["source"]["geometry"]["type"] == "MultiPoint" for layer in layers)
        )

    def test_right_inset_does_not_change_connection_camera(self):
        without_card = self.build_overlay(self.city_source, self.sight_target)
        with_card = self.build_overlay(
            self.city_source, self.sight_target, right_inset=280
        )

        self.assertEqual(with_card.center, without_card.center)
        self.assertEqual(with_card.zoom, without_card.zoom)

    def test_top_inset_places_full_region_connection_below_card(self):
        from acesta.stats.dash.interest.map_connections import build_arrow_curve
        from acesta.stats.dash.interest.map_connections import MAP_TILE_SIZE
        from acesta.stats.dash.interest.map_connections import _project_point

        top_inset = 150
        without_card = self.build_overlay(self.region_source, self.region_target)
        with_card = self.build_overlay(
            self.region_source,
            self.region_target,
            top_inset=top_inset,
        )
        curve = build_arrow_curve(self.region_source.anchor, self.region_target.anchor)
        projected_curve = tuple(_project_point(*point) for point in curve)
        arrow_center_y = (
            min(point[1] for point in projected_curve)
            + max(point[1] for point in projected_curve)
        ) / 2
        projected_center = _project_point(
            with_card.center["lon"], with_card.center["lat"]
        )
        world_size = MAP_TILE_SIZE * (2**with_card.zoom)
        arrow_screen_y = 300 + (arrow_center_y - projected_center[1]) * world_size

        self.assertAlmostEqual(arrow_screen_y, (top_inset + 64 + 600 - 64) / 2)
        self.assertLessEqual(with_card.zoom, without_card.zoom)

        entity_points = (
            self.region_source.fit_coordinates + self.region_target.fit_coordinates
        )
        screen_y = tuple(
            300 + (_project_point(*point)[1] - projected_center[1]) * world_size
            for point in entity_points
        )
        self.assertGreaterEqual(min(screen_y), top_inset + 64)
        self.assertLessEqual(max(screen_y), 600 - 64)

    def test_repeated_connection_builds_same_camera(self):
        first = self.build_overlay(self.region_source, self.region_target)
        repeated = self.build_overlay(self.region_source, self.region_target)

        self.assertEqual(first.center, repeated.center)
        self.assertEqual(first.zoom, repeated.zoom)

    def test_kamchatka_chukotka_arrow_is_centered_and_fully_visible(self):
        from shapely.geometry import MultiPolygon
        from shapely.geometry import Polygon

        from acesta.stats.dash.interest.map_connections import build_arrow_curve
        from acesta.stats.dash.interest.map_connections import create_region_entity
        from acesta.stats.dash.interest.map_connections import MAP_TILE_SIZE
        from acesta.stats.dash.interest.map_connections import _project_point

        kamchatka = create_region_entity(
            "41",
            "Камчатский край",
            Polygon([(158, 51), (163, 51), (163, 61), (158, 61)]),
        )
        chukotka = create_region_entity(
            "87",
            "Чукотский автономный округ",
            MultiPolygon(
                [
                    Polygon([(165, 62), (178, 62), (178, 72), (165, 72)]),
                    Polygon([(-180, 64), (-170, 64), (-170, 69), (-180, 69)]),
                ]
            ),
        )
        curve = build_arrow_curve(kamchatka.anchor, chukotka.anchor)
        projected_curve = tuple(_project_point(*point) for point in curve)
        expected_center_x = (
            min(point[0] for point in projected_curve)
            + max(point[0] for point in projected_curve)
        ) / 2
        expected_center_y = (
            min(point[1] for point in projected_curve)
            + max(point[1] for point in projected_curve)
        ) / 2

        for right_inset in (0, 180, 340):
            with self.subTest(right_inset=right_inset):
                overlay = self.build_overlay(
                    kamchatka,
                    chukotka,
                    right_inset=right_inset,
                )
                projected_center = _project_point(
                    overlay.center["lon"], overlay.center["lat"]
                )
                self.assertAlmostEqual(projected_center[0], expected_center_x)
                self.assertAlmostEqual(projected_center[1], expected_center_y)

                world_size = MAP_TILE_SIZE * (2**overlay.zoom)
                screen_points = tuple(
                    (
                        450 + (point[0] - projected_center[0]) * world_size,
                        300 + (point[1] - projected_center[1]) * world_size,
                    )
                    for point in projected_curve
                )
                self.assertGreaterEqual(min(point[0] for point in screen_points), 0)
                self.assertLessEqual(max(point[0] for point in screen_points), 900)
                self.assertGreaterEqual(min(point[1] for point in screen_points), 0)
                self.assertLessEqual(max(point[1] for point in screen_points), 600)

    def test_dateline_connection_uses_nearest_world_copy(self):
        from acesta.stats.dash.interest.map_connections import build_arrow_curve

        curve = build_arrow_curve((179, 60), (-179, 60))
        longitudes = [point[0] for point in curve]

        self.assertLess(max(longitudes) - min(longitudes), 5)


class InterestTargetStateTest(test.TestCase):
    def test_default_city_target_is_the_region_capital(self):
        from unittest import mock

        from acesta.stats.dash.interest import interest as interest_module

        queryset = mock.Mock()
        queryset.order_by.return_value.first.return_value = SimpleNamespace(pk=17)
        user = SimpleNamespace(current_region=SimpleNamespace(code="79"))

        with mock.patch.object(
            interest_module.City.objects,
            "filter",
            return_value=queryset,
        ) as city_filter:
            key = interest_module.get_default_target_key(user, "cities", "")

        self.assertEqual(key, "cities_17")
        city_filter.assert_called_once_with(code_id="79", is_capital=True)

    def test_default_sight_target_uses_largest_qty_then_primary_key(self):
        from unittest import mock

        from acesta.stats.dash.interest import interest as interest_module

        user = SimpleNamespace(current_region=SimpleNamespace(code="79"))

        with mock.patch.object(
            interest_module,
            "get_default_sight_target",
            return_value={"id": 35},
        ) as get_target:
            key = interest_module.get_default_target_key(user, "sights", "museum")

        self.assertEqual(key, "sights_35")
        get_target.assert_called_once_with("79", "museum")

    def test_explicit_region_transition_discards_saved_point_target(self):
        from acesta.stats.dash.interest import interest as interest_module

        result = interest_module.update_home_area_key(
            "regions",
            None,
            "museum",
            {
                "homeArea": "cities",
                "tourismType": "museum",
                "targetKey": "cities_17",
            },
            "cities_17",
            True,
            user=SimpleNamespace(
                current_region=SimpleNamespace(code="79"),
                is_extended=True,
            ),
            callback_context=SimpleNamespace(
                triggered=[{"prop_id": "home-area.value"}]
            ),
        )

        self.assertEqual(result, "regions_0")

    def test_region_transition_clears_source_but_preserves_global_context(self):
        from acesta.stats.dash.interest import interest as interest_module

        state = interest_module.save_interest_session_state(
            {
                "homeArea": "regions",
                "interesantArea": "cities",
                "tourismType": "museum",
                "sortBy": [{"column_id": "ppt_display", "direction": "desc"}],
                "targetKey": "regions_0",
                "mapContextKey": "79|regions|cities|museum|regions_0",
                "sourceRowId": None,
            },
            None,
            True,
            [{"id": "101", "code": "101"}],
            {},
            user=SimpleNamespace(
                current_region=SimpleNamespace(code="79"),
                is_extended=True,
            ),
        )

        self.assertEqual(state["targetKey"], "regions_0")
        self.assertIsNone(state["sourceRowId"])
        self.assertEqual(state["tourismType"], "museum")
        self.assertEqual(state["interesantArea"], "cities")
        self.assertEqual(
            state["sortBy"],
            [{"column_id": "ppt_display", "direction": "desc"}],
        )

    def test_region_transition_does_not_restore_initial_source_row(self):
        from unittest import mock

        import pandas as pd

        from acesta.stats.dash.interest import interest as interest_module

        table = pd.DataFrame(
            [
                {
                    "id": "27",
                    "code": "27",
                    "code__title": "Хабаровский край",
                }
            ]
        )
        initial_state = {
            "homeArea": "regions",
            "interesantArea": "regions",
            "tourismType": "",
            "sortBy": [{"column_id": "qty_display", "direction": "desc"}],
            "sourceRowId": "27",
        }
        with mock.patch.object(interest_module, "get_interest_table_rows"):
            with mock.patch.object(interest_module, "get_ppt_df", return_value=table):
                _, selected_cells, active_cell, _ = interest_module.update_interest(
                    "",
                    "regions",
                    "regions",
                    None,
                    "regions_0",
                    initial_state["sortBy"],
                    None,
                    initial_state,
                    True,
                    user=SimpleNamespace(
                        current_region=SimpleNamespace(code="79"),
                        is_extended=True,
                    ),
                    callback_context=SimpleNamespace(
                        triggered=[{"prop_id": "home-area-key.data"}]
                    ),
                )

        self.assertEqual(selected_cells, [])
        self.assertIsNone(active_cell)

    def test_empty_sights_balloon_uses_centered_low_interest_style(self):
        from acesta.stats.dash.interest.map import get_empty_sights_balloon

        balloon = get_empty_sights_balloon()

        self.assertIn("interest-map-balloon--popularity-low", balloon.className)
        self.assertIn("interest-map-balloon--empty", balloon.className)
        self.assertEqual(balloon.children.children, "Нет данных")

    def test_city_source_map_click_selects_table_row_for_region_target(self):
        from unittest import mock

        import pandas as pd

        from acesta.stats.dash.interest import interest as interest_module

        table = pd.DataFrame(
            [
                {
                    "id": "101",
                    "code": "101",
                    "code__title": "Хабаровск",
                    "qty": 100,
                    "ppt": 7.06,
                }
            ]
        )
        sort_states = (
            [],
            [{"column_id": "qty_display", "direction": "desc"}],
            [
                {"column_id": "qty_display", "direction": "desc"},
                {"column_id": "ppt_display", "direction": "asc"},
            ],
        )
        for sort_by in sort_states:
            with self.subTest(sort_by=sort_by):
                with mock.patch.object(interest_module, "get_interest_table_rows"):
                    with mock.patch.object(
                        interest_module, "get_ppt_df", return_value=table
                    ):
                        (
                            _,
                            selected_cells,
                            active_cell,
                            table_state,
                        ) = interest_module.update_interest(
                            "",
                            "regions",
                            "cities",
                            {"points": [{"id": "source-cities_101"}]},
                            "regions_0",
                            sort_by,
                            None,
                            user=SimpleNamespace(
                                current_region=SimpleNamespace(code="79"),
                                is_extended=True,
                            ),
                            callback_context=SimpleNamespace(
                                triggered=[{"prop_id": "map.clickData"}]
                            ),
                        )

                self.assertEqual(active_cell["row_id"], "101")
                self.assertEqual(len(selected_cells), 3)
                self.assertEqual(table_state["sortBy"], sort_by)

    def test_region_click_selects_source_without_replacing_point_target(self):
        from unittest import mock

        import pandas as pd
        from dash.exceptions import PreventUpdate

        from acesta.stats.dash.interest import interest as interest_module

        map_data = {"points": [{"location": "27"}]}
        callback_context = SimpleNamespace(triggered=[{"prop_id": "map.clickData"}])
        table = pd.DataFrame(
            [
                {
                    "id": "79",
                    "code": "79",
                    "code__title": "Еврейская автономная область",
                },
                {
                    "id": "27",
                    "code": "27",
                    "code__title": "Хабаровский край",
                },
            ]
        )

        for home_area in ("cities", "sights"):
            with self.subTest(home_area=home_area):
                with self.assertRaises(PreventUpdate):
                    interest_module.update_home_area_key(
                        home_area,
                        map_data,
                        "",
                        {},
                        f"{home_area}_10",
                        user=SimpleNamespace(
                            current_region=SimpleNamespace(code="79"),
                            is_extended=True,
                        ),
                        callback_context=callback_context,
                    )

                with mock.patch.object(
                    interest_module, "get_interest_table_rows"
                ) as get_interest:
                    with mock.patch.object(
                        interest_module, "get_ppt_df", return_value=table
                    ):
                        with mock.patch.object(
                            interest_module, "is_valid_target", return_value=True
                        ):
                            (
                                _,
                                selected_cells,
                                active_cell,
                                _,
                            ) = interest_module.update_interest(
                                "",
                                home_area,
                                "regions",
                                map_data,
                                f"{home_area}_10",
                                [],
                                None,
                                user=SimpleNamespace(
                                    current_region=SimpleNamespace(code="79"),
                                    is_extended=True,
                                ),
                                callback_context=callback_context,
                            )

                    self.assertEqual(get_interest.call_args.args[4], 10)
                    self.assertEqual(active_cell["row_id"], "27")
                    self.assertEqual(active_cell["row"], 1)
                    self.assertEqual(len(selected_cells), 3)

    def test_city_source_click_updates_only_the_left_table_in_point_modes(self):
        from unittest import mock

        import pandas as pd
        from dash.exceptions import PreventUpdate

        from acesta.stats.dash.interest import interest as interest_module

        map_data = {"points": [{"id": "source-cities_101"}]}
        callback_context = SimpleNamespace(triggered=[{"prop_id": "map.clickData"}])
        table = pd.DataFrame(
            [
                {
                    "id": "101",
                    "code": "101",
                    "code__title": "Хабаровск",
                    "qty": 100,
                    "ppt": 7.06,
                }
            ]
        )

        for home_area, target_key in (
            ("cities", "cities_22"),
            ("sights", "sights_22"),
        ):
            with self.subTest(home_area=home_area):
                with mock.patch.object(
                    interest_module, "get_interest_table_rows"
                ) as get_interest:
                    with mock.patch.object(
                        interest_module, "is_valid_target", return_value=True
                    ):
                        with mock.patch.object(
                            interest_module,
                            "get_ppt_df",
                            return_value=table,
                        ):
                            (
                                _,
                                selected_cells,
                                active_cell,
                                _,
                            ) = interest_module.update_interest(
                                "",
                                home_area,
                                "cities",
                                map_data,
                                target_key,
                                [],
                                None,
                                user=SimpleNamespace(
                                    current_region=SimpleNamespace(code="79"),
                                    is_extended=True,
                                ),
                                callback_context=callback_context,
                            )

                self.assertEqual(active_cell["row_id"], "101")
                self.assertEqual(len(selected_cells), 3)
                self.assertEqual(get_interest.call_args.args[4], 22)
                with self.assertRaises(PreventUpdate):
                    interest_module.update_home_area_key(
                        home_area,
                        map_data,
                        "",
                        {},
                        target_key,
                        user=SimpleNamespace(
                            current_region=SimpleNamespace(code="79"),
                            is_extended=True,
                        ),
                        callback_context=callback_context,
                    )

    def test_point_target_click_updates_table_without_waiting_for_store(self):
        from unittest import mock

        import pandas as pd

        from acesta.stats.dash.interest import interest as interest_module

        table = pd.DataFrame(
            [{"id": "27", "code": "27", "code__title": "Хабаровский край"}]
        )
        for home_area in ("cities", "sights"):
            with self.subTest(home_area=home_area):
                with mock.patch.object(
                    interest_module, "get_interest_table_rows"
                ) as get_interest:
                    with mock.patch.object(
                        interest_module, "get_ppt_df", return_value=table
                    ):
                        with mock.patch.object(
                            interest_module, "is_valid_target", return_value=True
                        ):
                            (
                                data,
                                selected_cells,
                                active_cell,
                                _,
                            ) = interest_module.update_interest(
                                "",
                                home_area,
                                "regions",
                                {"points": [{"id": f"{home_area}_22"}]},
                                f"{home_area}_10",
                                [],
                                None,
                                user=SimpleNamespace(
                                    current_region=SimpleNamespace(code="79"),
                                    is_extended=True,
                                ),
                                callback_context=SimpleNamespace(
                                    triggered=[{"prop_id": "map.clickData"}]
                                ),
                            )

                self.assertEqual(get_interest.call_args.args[4], 22)
                self.assertEqual(data[0]["code"], "27")
                self.assertEqual(selected_cells, [])
                self.assertIsNone(active_cell)

    def test_consecutive_point_clicks_use_each_clicked_target(self):
        from unittest import mock

        import pandas as pd

        from acesta.stats.dash.interest import interest as interest_module

        table = pd.DataFrame(
            [{"id": "27", "code": "27", "code__title": "Хабаровский край"}]
        )
        requested_ids = []
        for target_id in (22, 35):
            with mock.patch.object(
                interest_module, "get_interest_table_rows"
            ) as get_interest:
                with mock.patch.object(
                    interest_module, "get_ppt_df", return_value=table
                ):
                    with mock.patch.object(
                        interest_module, "is_valid_target", return_value=True
                    ):
                        interest_module.update_interest(
                            "",
                            "cities",
                            "regions",
                            {"points": [{"id": f"cities_{target_id}"}]},
                            "cities_10",
                            [],
                            None,
                            user=SimpleNamespace(
                                current_region=SimpleNamespace(code="79"),
                                is_extended=True,
                            ),
                            callback_context=SimpleNamespace(
                                triggered=[{"prop_id": "map.clickData"}]
                            ),
                        )
            requested_ids.append(get_interest.call_args.args[4])

        self.assertEqual(requested_ids, [22, 35])

    def test_unknown_region_click_keeps_current_selection(self):
        from unittest import mock

        import pandas as pd
        from dash.exceptions import PreventUpdate

        from acesta.stats.dash.interest import interest as interest_module

        with mock.patch.object(interest_module, "get_interest_table_rows"):
            with mock.patch.object(
                interest_module,
                "get_ppt_df",
                return_value=pd.DataFrame(
                    [{"id": "27", "code": "27", "code__title": "Хабаровский край"}]
                ),
            ):
                with mock.patch.object(
                    interest_module, "is_valid_target", return_value=True
                ):
                    with self.assertRaises(PreventUpdate):
                        interest_module.update_interest(
                            "",
                            "cities",
                            "regions",
                            {"points": [{"location": "missing"}]},
                            "cities_10",
                            [],
                            {"row": 0, "row_id": "27"},
                            user=SimpleNamespace(
                                current_region=SimpleNamespace(code="79"),
                                is_extended=True,
                            ),
                            callback_context=SimpleNamespace(
                                triggered=[{"prop_id": "map.clickData"}]
                            ),
                        )

    def test_area_change_resets_persistent_target(self):
        from unittest import mock

        from acesta.stats.dash.interest import interest as interest_module

        with mock.patch.object(
            interest_module,
            "get_default_target_key",
            return_value="sights_35",
        ):
            result = interest_module.update_home_area_key(
                "sights",
                {"points": [{"id": "cities_10"}]},
                "",
                {},
                "cities_10",
                True,
                user=SimpleNamespace(
                    current_region=SimpleNamespace(code="79"),
                    is_extended=True,
                ),
                callback_context=SimpleNamespace(
                    triggered=[{"prop_id": "home-area.value"}]
                ),
            )

        self.assertEqual(result, "sights_35")

    def test_valid_map_click_replaces_target(self):
        from unittest import mock

        from acesta.stats.dash.interest import interest as interest_module

        with mock.patch.object(
            interest_module,
            "is_valid_target",
            return_value=True,
        ):
            result = interest_module.update_home_area_key(
                "cities",
                {"points": [{"id": "cities_22"}]},
                "",
                {},
                "cities_10",
                user=SimpleNamespace(
                    current_region=SimpleNamespace(code="79"),
                    is_extended=True,
                ),
                callback_context=SimpleNamespace(
                    triggered=[{"prop_id": "map.clickData"}]
                ),
            )

        self.assertEqual(result, "cities_22")

    def test_table_query_uses_persistent_target_instead_of_stale_click(self):
        from unittest import mock

        import pandas as pd

        from acesta.stats.dash.interest import interest as interest_module

        table = pd.DataFrame(
            [{"id": "27", "code": "27", "code__title": "Хабаровский край"}]
        )
        with mock.patch.object(
            interest_module, "get_interest_table_rows"
        ) as get_interest:
            with mock.patch.object(interest_module, "get_ppt_df", return_value=table):
                with mock.patch.object(
                    interest_module, "is_valid_target", return_value=True
                ):
                    interest_module.update_interest(
                        "",
                        "cities",
                        "regions",
                        {"points": [{"id": "cities_10"}]},
                        "cities_22",
                        [],
                        None,
                        user=SimpleNamespace(
                            current_region=SimpleNamespace(code="79"),
                            is_extended=True,
                        ),
                        callback_context=SimpleNamespace(
                            triggered=[{"prop_id": "tourism-type.value"}]
                        ),
                    )

        self.assertEqual(get_interest.call_args.args[4], 22)

    def test_filtered_out_target_falls_back_to_largest_visible_sight(self):
        from unittest import mock

        import pandas as pd

        from acesta.stats.dash.interest import interest as interest_module

        with mock.patch.object(
            interest_module, "get_interest_table_rows"
        ) as get_interest:
            with mock.patch.object(
                interest_module,
                "get_ppt_df",
                return_value=pd.DataFrame(),
            ):
                with mock.patch.object(
                    interest_module, "is_valid_target", return_value=False
                ):
                    with mock.patch.object(
                        interest_module,
                        "get_default_target_key",
                        return_value="sights_35",
                    ):
                        interest_module.update_interest(
                            "museum",
                            "sights",
                            "regions",
                            None,
                            "sights_22",
                            [],
                            None,
                            user=SimpleNamespace(
                                current_region=SimpleNamespace(code="79"),
                                is_extended=True,
                            ),
                            callback_context=SimpleNamespace(
                                triggered=[{"prop_id": "tourism-type.value"}]
                            ),
                        )

        self.assertEqual(get_interest.call_args.args[4], 35)

    def test_city_source_selection_survives_table_callback(self):
        from unittest import mock

        import pandas as pd

        from acesta.stats.dash.interest import interest as interest_module

        table = pd.DataFrame(
            [
                {
                    "id": "101",
                    "code": "101",
                    "code__title": "Хабаровск",
                    "qty": 100,
                    "ppt": 7.06,
                }
            ]
        )
        with mock.patch.object(interest_module, "get_interest_table_rows"):
            with mock.patch.object(interest_module, "get_ppt_df", return_value=table):
                with mock.patch.object(
                    interest_module, "is_valid_target", return_value=True
                ):
                    _, selected_cells, active_cell, _ = interest_module.update_interest(
                        "",
                        "sights",
                        "cities",
                        None,
                        "sights_22",
                        [],
                        {"row": 0, "row_id": "101"},
                        user=SimpleNamespace(
                            current_region=SimpleNamespace(code="79"),
                            is_extended=True,
                        ),
                        callback_context=SimpleNamespace(
                            triggered=[{"prop_id": "table-interesants.active_cell"}]
                        ),
                    )

        self.assertEqual(active_cell["row_id"], "101")
        self.assertEqual(len(selected_cells), 3)


class InterestMapConnectionCallbackTest(test.TestCase):
    def test_sight_markers_prefetch_groups_with_their_existing_query(self):
        from acesta.stats.dash.helpers.interest import get_sights

        self.assertEqual(list(get_sights("__", "")), [])

    def test_callback_supports_all_six_source_target_combinations(self):
        from unittest import mock

        import geopandas as gpd
        from django.conf import settings
        from shapely.geometry import Polygon

        from acesta.stats.dash.interest import map as map_module
        from acesta.stats.dash.interest.map_connections import ARROW_COLOR

        map_data = gpd.GeoDataFrame(
            {
                "name": [
                    "Еврейская автономная область",
                    "Хабаровский край",
                    "Саратовская область",
                ],
                "qty": [19276, 999, 0],
                "ppt": [36737, 1636, 0],
                "geometry": [
                    Polygon([(131, 47), (133, 47), (133, 49), (131, 49)]),
                    Polygon([(134, 48), (136, 48), (136, 50), (134, 50)]),
                    Polygon([(45, 50), (47, 50), (47, 52), (45, 52)]),
                ],
            },
            index=["79", "27", "64"],
            crs="EPSG:4326",
        )
        current_region = SimpleNamespace(
            code="79",
            title="Еврейская автономная область",
            rank=2,
            center_lat=48.5,
            center_lon=132,
            zoom_regions=4,
            zoom_cities=6,
            get_federal_district_display=lambda: "Дальневосточный",
            get_rank_display=lambda: "Средний",
        )
        user = SimpleNamespace(current_region=current_region, is_extended=True)
        request = SimpleNamespace(COOKIES={"innerHeight": "768"}, user=user)
        source_city = SimpleNamespace(
            pk=101,
            id=101,
            title="Хабаровск",
            lon=135.07,
            lat=48.48,
            population=617000,
            code=SimpleNamespace(title="Хабаровский край"),
        )
        target_city = SimpleNamespace(
            pk=201,
            id=201,
            title="Биробиджан",
            lon=132.92,
            lat=48.79,
            population=68000,
        )
        target_sight = SimpleNamespace(
            pk=301,
            id=301,
            title="Набережная",
            lon=132.91,
            lat=48.80,
            qty=100,
            address="Россия, ул. Набережная",
            group=SimpleNamespace(all=lambda: []),
        )
        sources = (
            (
                settings.AREA_REGIONS,
                {
                    "id": "27",
                    "code": "27",
                    "code__title": "Хабаровский край",
                    "qty": 999,
                    "ppt": 16.36,
                },
            ),
            (
                settings.AREA_CITIES,
                {
                    "id": "101",
                    "code": "101",
                    "code__title": "Хабаровск",
                    "qty": 1000,
                    "ppt": 7.06,
                },
            ),
        )
        targets = (
            (settings.AREA_REGIONS, "regions_0", 1),
            (settings.AREA_CITIES, "cities_201", 1),
            (settings.AREA_SIGHTS, "sights_301", 1),
        )
        city_filter = SimpleNamespace(
            exists=lambda: True,
            first=lambda: source_city,
        )

        for home_area, target_key, balloon_count in targets:
            for interesant_area, row in sources:
                with self.subTest(
                    source=interesant_area,
                    target=home_area,
                ):
                    with mock.patch.object(
                        map_module,
                        "get_map_df",
                        return_value=map_data.copy(),
                    ):
                        with mock.patch.object(
                            map_module,
                            "get_cities",
                            return_value=[target_city, source_city],
                        ):
                            with mock.patch.object(
                                map_module,
                                "get_sights",
                                return_value=[target_sight],
                            ):
                                with mock.patch.object(
                                    map_module,
                                    "get_city_heatmap_items",
                                    return_value=[(source_city, row)],
                                ):
                                    with mock.patch.object(
                                        map_module.City.objects,
                                        "filter",
                                        return_value=city_filter,
                                    ):
                                        with mock.patch.object(
                                            map_module,
                                            "resolve_target_key",
                                            return_value=target_key,
                                        ):
                                            table_state = {
                                                "homeArea": home_area,
                                                "interesantArea": interesant_area,
                                                "tourismType": "",
                                                "targetKey": target_key,
                                                "mapContextKey": (
                                                    f"79|{home_area}|"
                                                    f"{interesant_area}||{target_key}"
                                                ),
                                                "sourceRowId": row["id"],
                                            }
                                            figure, _, balloons = map_module.update_map(
                                                table_state,
                                                {
                                                    "row": 0,
                                                    "row_id": row["id"],
                                                },
                                                "",
                                                home_area,
                                                interesant_area,
                                                target_key,
                                                {
                                                    "width": 900,
                                                    "height": 600,
                                                    "rightInset": 220,
                                                },
                                                [row],
                                                user=user,
                                                request=request,
                                            )

                    self.assertEqual(len(balloons), balloon_count)
                    roles = {
                        balloon.to_plotly_json()["props"]["data-role"]
                        for balloon in balloons
                    }
                    self.assertIn("source", roles)
                    self.assertNotIn("target", roles)
                    source_balloon = next(
                        balloon
                        for balloon in balloons
                        if balloon.to_plotly_json()["props"]["data-role"] == "source"
                    )
                    source_children = source_balloon.to_plotly_json()["props"][
                        "children"
                    ]
                    if interesant_area == settings.AREA_REGIONS:
                        metric = source_children[-1]
                        self.assertEqual(
                            metric.className, "interest-map-balloon__metric"
                        )
                        self.assertEqual(metric.children[0], "очень высокая,")
                        self.assertEqual(
                            metric.children[1].to_plotly_json()["type"], "Br"
                        )
                        self.assertEqual(metric.children[2], "но аудитория ограничена")
                    else:
                        self.assertEqual(source_children[-1].children, "высокая")
                    if interesant_area == settings.AREA_REGIONS:
                        region_trace = next(
                            trace
                            for trace in figure.data
                            if trace.type == "choroplethmap"
                            and "27" in list(trace.locations)
                        )
                        region_position = list(region_trace.locations).index("27")
                        self.assertEqual(
                            list(region_trace.customdata[region_position]),
                            [
                                "Хабаровский край",
                                "очень высокая,<br>но аудитория ограничена",
                            ],
                        )
                        no_data_position = list(region_trace.locations).index("64")
                        self.assertEqual(
                            list(region_trace.customdata[no_data_position]),
                            ["Саратовская область", "нет данных"],
                        )
                        if home_area == settings.AREA_REGIONS:
                            self.assertEqual(region_trace.z[no_data_position], -1)
                            self.assertEqual(region_trace.zmin, -1)
                            self.assertEqual(
                                region_trace.colorscale[0][1],
                                "#ffffff",
                            )
                            self.assertEqual(
                                region_trace.marker.line.color,
                                "#d3dde0",
                            )
                    else:
                        city_source_trace = next(
                            trace
                            for trace in figure.data
                            if getattr(trace, "ids", None)
                            and str(trace.ids[0]).startswith("source-cities_")
                        )
                        self.assertEqual(
                            list(city_source_trace.customdata[0]),
                            ["Хабаровский край", "популярность высокая"],
                        )
                        self.assertEqual(
                            city_source_trace.hoverlabel.bgcolor[0], "#7cbbb0"
                        )
                    if home_area in (settings.AREA_CITIES, settings.AREA_SIGHTS):
                        target_trace = next(
                            trace
                            for trace in figure.data
                            if getattr(trace, "ids", None)
                            and str(trace.ids[0]).startswith(f"{home_area}_")
                        )
                        self.assertEqual(target_trace.marker.opacity, 1)
                    if (
                        interesant_area == settings.AREA_CITIES
                        and home_area != settings.AREA_REGIONS
                    ):
                        background = figure.data[0]
                        self.assertEqual(background.type, "choroplethmap")
                        self.assertEqual(background.marker.opacity, 0.45)
                        self.assertEqual(figure.layout.map.style, "open-street-map")
                        trace_ids = [
                            list(trace.ids)
                            for trace in figure.data
                            if getattr(trace, "ids", None) is not None
                        ]
                        self.assertTrue(trace_ids[0][0].startswith("source-cities_"))
                        self.assertFalse(trace_ids[-1][0].startswith("source-"))
                    self.assertTrue(
                        any(
                            layer.color == ARROW_COLOR
                            and layer.source.get("geometry", {}).get("type")
                            == "LineString"
                            and layer.line.width == 4
                            for layer in figure.layout.map.layers
                        )
                    )
