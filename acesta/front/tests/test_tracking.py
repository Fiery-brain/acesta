from django import test

from acesta.front.tracking import build_tracking_url


class TrackingURLTest(test.SimpleTestCase):
    def test_builds_tracking_url_and_preserves_query_and_fragment(self):
        result = build_tracking_url(
            "/landing/?existing=value#details",
            source="newsletter",
            medium="email",
            campaign="summer",
            content="button",
            dimensions={"segment": "tour operators", "region": "66"},
        )

        self.assertEqual(
            result,
            "/landing/?existing=value"
            "&utm_source=newsletter"
            "&utm_medium=email"
            "&utm_campaign=summer"
            "&utm_content=button"
            "&segment=tour+operators"
            "&region=66"
            "#details",
        )

    def test_requires_target_and_removes_empty_dimensions(self):
        with self.assertRaises(ValueError):
            build_tracking_url(
                None,
                source="site",
                medium="link",
                campaign="help",
                content="header",
            )

        result = build_tracking_url(
            "/?segment=old&region=old",
            source="site",
            medium="link",
            campaign="help",
            content="header",
            dimensions={"segment": None, "region": ""},
        )

        self.assertEqual(
            result,
            "/?utm_source=site&utm_medium=link&utm_campaign=help&utm_content=header",
        )

    def test_removes_empty_utm_values_already_present_in_query(self):
        result = build_tracking_url(
            "/?utm_source=old&utm_medium=old&utm_campaign=old&utm_content=old",
            source="site",
            medium=None,
            campaign="",
            content="header",
        )

        self.assertEqual(result, "/?utm_source=site&utm_content=header")
