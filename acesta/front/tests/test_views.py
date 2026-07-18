from django import test
from django.conf import settings
from django.urls import reverse

from acesta.front.utils import get_segment_market
from acesta.front.utils import get_segment_pattern


class FrontTest(test.TestCase):
    def test_responses(self):
        """
        Testing of the front
        :return: None
        """
        # index
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)

        # sitemap
        response = self.client.get(reverse("sitemap"))
        self.assertEqual(response.status_code, 200)
        for segment in (
            settings.SEGMENT_GOVERNMENT,
            settings.SEGMENT_TIC,
            settings.SEGMENT_TOUR_OPERATOR,
        ):
            self.assertContains(response, f"/{segment}/")
        self.assertContains(response, "<priority>0.90</priority>")

        # robots
        response = self.client.get(reverse("robots"))
        self.assertEqual(response.status_code, 200)

        # help
        response = self.client.get(reverse("help"))
        self.assertEqual(response.status_code, 200)

        # terms
        response = self.client.get(reverse("terms"))
        self.assertEqual(response.status_code, 200)

        # privacy
        response = self.client.get(reverse("privacy"))
        self.assertEqual(response.status_code, 200)

    def test_segment_market_mapping(self):
        self.assertEqual(
            get_segment_market(settings.SEGMENT_GOVERNMENT),
            settings.MARKET_B2G,
        )
        self.assertEqual(get_segment_market(settings.SEGMENT_TIC), settings.MARKET_B2G)
        self.assertEqual(
            get_segment_market(settings.SEGMENT_TOUR_OPERATOR),
            settings.MARKET_B2B,
        )
        self.assertEqual(
            get_segment_market(settings.SEGMENT_HOSPITALITY),
            settings.MARKET_B2B,
        )
        self.assertEqual(
            get_segment_market(settings.DEFAULT_SEGMENT),
            settings.MARKET_B2B,
        )
        self.assertEqual(get_segment_market("unknown-segment"), settings.MARKET_B2B)
        self.assertEqual(get_segment_market(None), settings.MARKET_B2B)

    def test_segment_pattern_contains_segment_landing_slugs(self):
        pattern = get_segment_pattern()
        for segment in (
            settings.SEGMENT_GOVERNMENT,
            settings.SEGMENT_TIC,
            settings.SEGMENT_TOUR_OPERATOR,
            settings.SEGMENT_TOUR_AGENT,
            settings.SEGMENT_TOURISM_PRODUCT_OWNER,
            settings.SEGMENT_INVESTORS,
            settings.SEGMENT_GUIDE,
            settings.SEGMENT_MARKETING_AGENCY,
            settings.SEGMENT_HOSPITALITY,
            settings.SEGMENT_TOURISM_EVENT,
            settings.SEGMENT_TRANSPORTATION,
        ):
            self.assertRegex(segment, rf"^({pattern})$")
