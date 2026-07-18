from unittest import mock

from django import test
from django.contrib.auth import get_user
from django.urls import reverse

from acesta.user.helpers import CredentialsMixin


class CommercialOfferPDFTest(CredentialsMixin, test.TestCase):
    def setUp(self):
        super().setUp()
        self.client.login(**self.credentials)
        self.user = get_user(self.client)

    def test_offer_requires_authentication(self):
        self.client.logout()

        response = self.client.get(reverse("offer"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    @mock.patch("acesta.user.views.user.send_message")
    @mock.patch("acesta.front.pdf.response.render_pdf", return_value=b"%PDF-test")
    def test_offer_returns_pdf_by_default(self, render, send):
        response = self.client.get(reverse("offer"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn(
            f"acesta-offer-{self.user.current_region.code}-",
            response["Content-Disposition"],
        )
        render.assert_called_once()
        self.assertEqual(render.call_args.kwargs["profile"], "a4")
        send.assert_called_once()

    @mock.patch("acesta.user.views.user.send_message")
    @mock.patch("acesta.front.pdf.response.render_pdf")
    def test_offer_can_return_html_without_pdf_or_notification(self, render, send):
        response = self.client.get(reverse("offer"), {"format": "html"})
        html = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/html"))
        self.assertIn(self.user.current_region.title, html)
        self.assertIn("/static/css/pdf_documents.css", html)
        self.assertIn("/static/img/acesta-ru-full.png", html)
        self.assertNotIn("data:", html)
        self.assertIn('class="pdf-page pdf-document-page"', html)
        render.assert_not_called()
        send.assert_not_called()

    @mock.patch("acesta.front.pdf.response.render_pdf")
    def test_offer_rejects_unknown_format(self, render):
        response = self.client.get(reverse("offer"), {"format": "docx"})

        self.assertEqual(response.status_code, 400)
        render.assert_not_called()

    @mock.patch("acesta.user.views.user.send_message")
    @mock.patch("acesta.front.pdf.response.render_pdf", return_value=b"%PDF-test")
    def test_report_offer_returns_pdf_by_default(self, render, send):
        response = self.client.get(reverse("offer_report"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn(
            f"acesta-offer-report-{self.user.current_region.code}-",
            response["Content-Disposition"],
        )
        render.assert_called_once()
        send.assert_called_once()

    @mock.patch("acesta.user.views.user.send_message")
    @mock.patch("acesta.front.pdf.response.render_pdf")
    def test_report_offer_can_return_html(self, render, send):
        response = self.client.get(reverse("offer_report"), {"format": "html"})
        html = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Аналитический отчет", html)
        self.assertIn(self.user.current_region.title, html)
        render.assert_not_called()
        send.assert_not_called()

    @mock.patch("acesta.user.views.user.send_message")
    @mock.patch("acesta.front.pdf.response.render_pdf", return_value=b"%PDF-test")
    def test_public_offer_returns_pdf_without_authentication(self, render, send):
        self.client.logout()

        response = self.client.get(reverse("oferta"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn(
            "attachment; filename=acesta-offer-", response["Content-Disposition"]
        )
        render.assert_called_once()
        send.assert_called_once()

    @mock.patch("acesta.user.views.user.send_message")
    @mock.patch("acesta.front.pdf.response.render_pdf")
    def test_public_offer_can_return_html_without_notification(self, render, send):
        self.client.logout()

        response = self.client.get(reverse("oferta"), {"format": "html"})
        html = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("ОФЕРТА", html)
        self.assertIn("/static/css/pdf_documents.css", html)
        self.assertNotIn("data:", html)
        self.assertEqual(html.count('class="pdf-document-page"'), 4)
        render.assert_not_called()
        send.assert_not_called()

    @mock.patch("acesta.front.pdf.response.render_pdf")
    def test_public_offer_rejects_unknown_format(self, render):
        self.client.logout()

        response = self.client.get(reverse("oferta"), {"format": "docx"})

        self.assertEqual(response.status_code, 400)
        render.assert_not_called()
