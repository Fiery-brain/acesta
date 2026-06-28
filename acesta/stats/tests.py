from datetime import date
from pathlib import Path
from types import SimpleNamespace

from dateutil.relativedelta import relativedelta
from django import test
from django.contrib.auth import get_user
from django.template import Context
from django.template import Template
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
from acesta.stats.helpers.rating import get_rating_place_change
from acesta.stats.helpers.rating import get_synced_region_rating_places
from acesta.stats.helpers.sights import get_strong_tourism_types
from acesta.stats.helpers.sights import get_weak_tourism_types
from acesta.stats.models import RegionRating
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


class HistoryMixinTest(test.SimpleTestCase):
    def test_previous_history_item_uses_previous_month(self):
        rating = RegionRating(
            date=date(2026, 6, 28),
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
            history=[
                {"date": "2026-01-10", "place": 7},
                {"date": "2025-12-23", "place": 10},
            ],
        )

        self.assertEqual(
            rating.previous_history_item, {"date": "2025-12-23", "place": 10}
        )

    def test_previous_history_item_returns_empty_without_exact_previous_month(self):
        rating = RegionRating(
            date=date(2026, 6, 16),
            history=[
                {"date": "2026-06-10", "place": 7},
                {"date": "2026-04-20", "place": 10},
            ],
        )

        self.assertEqual(rating.previous_history_item, {})

    def test_previous_history_item_returns_empty_dict_without_history(self):
        rating = RegionRating(date=date(2026, 2, 16), history=[])

        self.assertEqual(rating.previous_history_item, {})

    def test_get_previous_history_value_uses_default(self):
        rating = RegionRating(date=date(2026, 2, 16), history=[])

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
        RegionRating.objects.filter(pk=rating_rec.pk).update(date=date(2026, 2, 16))

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
        RegionRating.objects.filter(pk=rating_rec.pk).update(date=date(2026, 2, 16))

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
            history=[{"date": "2026-01-20", "place": 7}],
        )

        self.assertEqual(get_rating_place_change(rating), -3)

    def test_rating_place_change_zero_when_place_does_not_change(self):
        rating = RegionRating(
            place=7,
            date=date(2026, 2, 16),
            history=[{"date": "2026-01-20", "place": 7}],
        )

        self.assertEqual(get_rating_place_change(rating), 0)

    def test_rating_place_change_none_without_history(self):
        rating = RegionRating(place=7, date=date(2026, 2, 16), history=[])

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
            Path(__file__).resolve().parents[1] / "templates/dashboard/rating.html"
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
            Path(__file__).resolve().parents[1] / "templates/dashboard/rating.html"
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
