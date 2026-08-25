from html import unescape

from django import test
from django.conf import settings
from django.template import Context
from django.template import Template
from django.urls import resolve
from django.urls import Resolver404
from django.urls import reverse

from acesta.front.qr.generator import generate_qr
from acesta.front.qr.generator import validate_qr_target
from acesta.user.models import User


class QRGeneratorTest(test.SimpleTestCase):
    def test_svg_is_deterministic_vector_with_rounded_modules_and_logo(self):
        target_url = f"https://{settings.PUBLIC_DOMAIN}/hub/?existing=value"

        first = generate_qr(target_url)
        second = generate_qr(target_url)

        self.assertEqual(first, second)
        self.assertEqual(first.url, target_url)
        self.assertIn("<circle", first.svg)
        self.assertIn("<path", first.svg)
        self.assertIn('fill="#FFBA0C"', first.svg)
        self.assertIn('fill="#066255"', first.svg)
        self.assertIn('fill="#C44D63"', first.svg)
        self.assertIn("<metadata>", first.svg)
        self.assertNotIn("<image", first.svg)
        self.assertIn(target_url, first.svg)
        self.assertNotIn("utm_", first.url)

    def test_caption_can_be_changed_or_hidden(self):
        default = generate_qr(f"https://{settings.PUBLIC_DOMAIN}/")
        custom = generate_qr("/dashboard/", caption="Открыть аналитику")
        hidden = generate_qr("/dashboard/", show_caption=False)

        self.assertIn('font-size="66"', default.svg)
        self.assertIn("Открыть аналитику", unescape(custom.svg))
        self.assertNotIn("<text", hidden.svg)

    def test_target_validation(self):
        self.assertEqual(validate_qr_target("/dashboard/"), "/dashboard/")
        with self.assertRaises(ValueError):
            validate_qr_target(None)
        self.assertEqual(
            validate_qr_target(f"https://{settings.PUBLIC_DOMAIN}/landing/"),
            f"https://{settings.PUBLIC_DOMAIN}/landing/",
        )
        for target in ("landing", "//example.com", "file:///tmp/private"):
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    validate_qr_target(target)


class QRTemplateTagTest(test.SimpleTestCase):
    def test_renders_qr_for_regular_html_template(self):
        template = Template("{% load qr %}{% qr_svg target caption=caption %}")

        content = template.render(
            Context({"target": "/help/", "caption": "Открыть сайт"})
        )

        self.assertIn("<svg", content)
        self.assertIn("/help/", content)
        self.assertIn("Открыть сайт", content)
        self.assertNotIn("utm_", content)


class QRViewTest(test.TestCase):
    fixtures = ["acesta/geo/fixtures/region.yaml"]

    def setUp(self):
        self.staff = User.objects.create_user(
            email="qr-staff@example.com",
            username="qr-staff@example.com",
            password="secret",
            region_id="01",
            registered=True,
            is_staff=True,
        )

    def test_route_is_general_and_old_pdf_route_is_removed(self):
        match = resolve("/qr.svg")

        self.assertEqual(match.url_name, "qr_svg")
        self.assertEqual(reverse("qr_svg"), "/qr.svg")
        with self.assertRaises(Resolver404):
            resolve("/pdf/qr.svg")

    def test_requires_staff_and_validates_parameters(self):
        response = self.client.get(reverse("qr_svg"))
        self.assertEqual(response.status_code, 302)

        self.client.force_login(self.staff)
        response = self.client.get(
            reverse("qr_svg"),
            {
                "target": f"https://{settings.PUBLIC_DOMAIN}/hub/?existing=value",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/svg+xml; charset=utf-8")
        self.assertIn(b"<svg", response.content)
        self.assertIn(b"existing=value", response.content)
        self.assertNotIn(b"utm_", response.content)

        invalid = self.client.get(
            reverse("qr_svg"),
            {"target": "file:///tmp/private"},
        )
        self.assertEqual(invalid.status_code, 400)
