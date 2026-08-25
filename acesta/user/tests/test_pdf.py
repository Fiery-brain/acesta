from html import escape
from unittest import mock
from urllib.parse import unquote

from django import test
from django.conf import settings
from django.contrib.auth import get_user
from django.urls import reverse
from django.utils import timezone

from acesta.user.helpers import CredentialsMixin
from acesta.user.models import AccessPromotion
from acesta.user.models import AccessPromotionCode


class CommercialOfferPDFTest(CredentialsMixin, test.TestCase):
    def setUp(self):
        super().setUp()
        self.client.login(**self.credentials)
        self.user = get_user(self.client)

    def assert_pdf_filename(self, response, expected):
        disposition = response["Content-Disposition"]
        self.assertTrue(disposition.startswith("inline; filename*=utf-8''"))
        self.assertEqual(unquote(disposition.partition("''")[2]), expected)

    def test_offer_document_routes_use_folder_html_and_pdf_extension(self):
        self.assertEqual(reverse("offer"), "/offer/")
        self.assertEqual(reverse("offer_pdf"), "/offer.pdf")
        self.assertEqual(reverse("offer_report"), "/offer-report/")
        self.assertEqual(reverse("offer_report_pdf"), "/offer-report.pdf")
        self.assertEqual(reverse("oferta"), "/oferta/")
        self.assertEqual(reverse("oferta_pdf"), "/oferta.pdf")

    def test_offer_requires_authentication(self):
        self.client.logout()

        response = self.client.get(reverse("offer"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    @mock.patch("acesta.user.views.user.send_message")
    @mock.patch("acesta.front.pdf.response.render_pdf", return_value=b"%PDF-test")
    def test_offer_pdf_route_returns_pdf(self, render, send):
        response = self.client.get(reverse("offer_pdf"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assert_pdf_filename(
            response,
            "Коммерческое предложение — ацеста — "
            f"{timezone.localdate().strftime('%d.%m.%Y')}.pdf",
        )
        render.assert_called_once()
        self.assertEqual(render.call_args.kwargs["profile"], "a4")
        rendered_html = render.call_args.args[0]
        self.assertEqual(rendered_html.count('data-commercial-offer-page="'), 3)
        self.assertIn('data-commercial-offer-page="1"', rendered_html)
        self.assertIn('data-commercial-offer-page="2"', rendered_html)
        self.assertIn('data-commercial-offer-page="3"', rendered_html)
        send.assert_called_once()

    @mock.patch("acesta.user.views.user.send_message")
    @mock.patch("acesta.front.pdf.response.render_pdf")
    def test_offer_can_return_html_without_pdf_or_notification(self, render, send):
        response = self.client.get(reverse("offer"))
        html = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/html"))
        self.assertIn(self.user.current_region.title, html)
        self.assertIn(
            "<title>Аналитический сервис ацеста. Коммерческое предложение "
            f"для региона {self.user.current_region.title}</title>",
            html,
        )
        self.assertIn("/static/css/pdf_documents.css", html)
        self.assertIn("/static/css/commercial_offer.css", html)
        self.assertIn("/static/img/pdf/acesta-logo.svg", html)
        self.assertNotIn("/static/img/pdf/acesta-logo-footer.svg", html)
        self.assertEqual(html.count("/static/img/pdf/acesta-logo.svg"), 3)
        self.assertNotIn('class="commercial-offer-waves"', html)
        self.assertNotIn("/static/img/acesta-ru.png", html)
        self.assertIn("/static/img/bg_welcome_to_acesta.svg", html)
        self.assertIn("/static/img/balloon.svg", html)
        self.assertIn("/static/img/pdf/icon-goal.svg", html)
        self.assertIn("/static/img/pdf/icon-path.svg", html)
        self.assertIn("/static/img/pdf/icon-trophy.svg", html)
        self.assertIn('class="commercial-offer-page-two"', html)
        self.assertEqual(html.count('class="commercial-offer-feature-card '), 3)
        self.assertIn('class="commercial-offer-ai-card"', html)
        self.assertIn('class="commercial-offer-history-card"', html)
        self.assertIn("Наши возможности", html)
        self.assertIn("commercial-offer-feature-card--region", html)
        self.assertIn("commercial-offer-feature-card--heart", html)
        self.assertIn("commercial-offer-feature-card--attract", html)
        self.assertNotIn("data:", html)
        self.assertEqual(html.count('data-commercial-offer-page="'), 3)
        self.assertEqual(html.count('class="commercial-offer-header"'), 3)
        self.assertEqual(html.count('class="commercial-offer-footer"'), 3)
        self.assertIn(
            f"acesta-segment-theme-{self.user.segment}",
            html,
        )
        self.assertIn('data-commercial-offer-segment="', html)
        self.assertEqual(html.count('class="commercial-offer-page__field"'), 3)
        self.assertIn("Варианты подключения", html)
        self.assertIn("Уровни доступа", html)
        self.assertIn('data-access-level-section="pricing"', html)
        self.assertIn('data-access-level-columns="full"', html)
        self.assertNotIn("data-access-level-action", html)
        self.assertIn("Почему мы", html)
        self.assertIn("89 регионов РФ", html)
        self.assertIn("12 видов туризма", html)
        self.assertIn("Начать просто!", html)
        application_url = (
            f"https://{settings.PUBLIC_DOMAIN}"
            f'{reverse("user_order_region", kwargs={"code": self.user.current_region.code})}'
        )
        tracking_query = (
            "utm_source=commercial-offer&amp;utm_medium=general&amp;"
            "utm_campaign=full-access&amp;utm_content="
        )
        header_url = f"{application_url}?{tracking_query}header-logo"
        qr_url = f"{application_url}?{tracking_query}qr"
        self.assertIn(f"<metadata>{qr_url}</metadata>", html)
        self.assertEqual(html.count(f'href="{header_url}"'), 3)
        self.assertEqual(html.count(f'href="{qr_url}"'), 1)
        for page_number in range(1, 4):
            footer_url = f"{application_url}?{tracking_query}page_{page_number}"
            self.assertEqual(html.count(f'href="{footer_url}"'), 2)
        self.assertNotIn(f'href="{application_url}"', html)
        self.assertFalse(response.has_header("Content-Disposition"))
        render.assert_not_called()
        send.assert_not_called()

    def test_offer_tracking_uses_user_segment(self):
        self.user.segment = settings.SEGMENT_GOVERNMENT
        self.user.save(update_fields=["segment"])

        response = self.client.get(reverse("offer"))
        html = response.content.decode()

        application_url = (
            f"https://{settings.PUBLIC_DOMAIN}"
            f'{reverse("user_order_region", kwargs={"code": self.user.current_region.code})}'
        )
        tracking_url = (
            f"{application_url}?utm_source=commercial-offer"
            f"&utm_medium={settings.SEGMENT_GOVERNMENT}"
            "&utm_campaign=full-access&utm_content="
        )
        self.assertIn(f"<metadata>{escape(tracking_url + 'qr')}</metadata>", html)
        self.assertEqual(
            html.count(f'href="{escape(tracking_url + "header-logo")}"'), 3
        )
        for page_number in range(1, 4):
            footer_url = escape(tracking_url + f"page_{page_number}")
            self.assertEqual(html.count(f'href="{footer_url}"'), 2)

    def test_offer_access_table_shows_active_promotion(self):
        promotion = AccessPromotion.objects.create(
            title="До конца месяца",
            discount=30,
            is_active=True,
        )
        AccessPromotionCode.objects.create(
            promotion=promotion,
            segment=settings.DEFAULT_SEGMENT,
            code="DEFAULT030",
        )

        response = self.client.get(reverse("offer"))
        html = response.content.decode()

        self.assertContains(response, "data-access-level-promotion")
        self.assertContains(response, 'data-promotion-discount="30"')
        self.assertContains(response, "До&nbsp;конца месяца")
        self.assertNotContains(response, "DEFAULT030")
        self.assertIn("<del>", html)
        self.assertIn('class="sale"', html)
        self.assertNotIn("data-access-level-action", html)
        self.assertEqual(html.count('class="waves"'), 1)
        waves_start = html.index('<svg class="waves"')
        waves_html = html[waves_start : html.index("</svg>", waves_start) + 6]
        self.assertEqual(waves_html.count("<animateTransform"), 4)

    @mock.patch("acesta.user.views.user.send_message")
    @mock.patch("acesta.front.pdf.response.render_pdf")
    def test_offer_query_format_does_not_control_html_url(self, render, send):
        response = self.client.get(reverse("offer"), {"format": "pdf"})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/html"))
        render.assert_not_called()
        send.assert_not_called()

    @mock.patch("acesta.user.views.user.send_message")
    @mock.patch("acesta.front.pdf.response.render_pdf", return_value=b"%PDF-test")
    def test_offer_query_format_does_not_control_pdf_url(self, render, send):
        response = self.client.get(reverse("offer_pdf"), {"format": "html"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        render.assert_called_once()
        send.assert_called_once()

    @mock.patch("acesta.user.views.user.send_message")
    @mock.patch("acesta.front.pdf.response.render_pdf", return_value=b"%PDF-test")
    def test_report_offer_pdf_route_returns_pdf(self, render, send):
        response = self.client.get(reverse("offer_report_pdf"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assert_pdf_filename(
            response,
            "Коммерческое предложение на аналитический отчёт — ацеста — "
            f"{timezone.localdate().strftime('%d.%m.%Y')}.pdf",
        )
        render.assert_called_once()
        send.assert_called_once()

    @mock.patch("acesta.user.views.user.send_message")
    @mock.patch("acesta.front.pdf.response.render_pdf")
    def test_report_offer_can_return_html(self, render, send):
        response = self.client.get(reverse("offer_report"))
        html = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Аналитический отчет", html)
        self.assertIn(self.user.current_region.title, html)
        self.assertIn(
            "<title>Аналитический сервис ацеста. Коммерческое предложение "
            "на аналитический отчёт</title>",
            html,
        )
        self.assertIn('data-access-level-section="pricing"', html)
        self.assertIn('data-access-level-columns="report"', html)
        self.assertIn("Срок выполнения", html)
        self.assertIn("1 месяц", html)
        self.assertIn("от 100 000 ₽", html)
        self.assertNotIn("1 вид туризма", html)
        self.assertFalse(response.has_header("Content-Disposition"))
        render.assert_not_called()
        send.assert_not_called()

    def test_price_page_links_to_pdf_documents(self):
        response = self.client.get(reverse("price"))

        self.assertContains(response, f'href="{reverse("oferta_pdf")}"')
        self.assertContains(response, f'href="{reverse("offer_pdf")}"')
        self.assertNotContains(response, 'href="/oferta/"')
        self.assertNotContains(response, 'href="/offer/"')

    @mock.patch("acesta.user.views.user.send_message")
    @mock.patch("acesta.front.pdf.response.render_pdf", return_value=b"%PDF-test")
    def test_public_offer_pdf_route_returns_pdf_without_authentication(
        self,
        render,
        send,
    ):
        self.client.logout()

        response = self.client.get(reverse("oferta_pdf"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assert_pdf_filename(
            response,
            "Оферта на оказание услуг — ацеста — "
            f"{timezone.localdate().strftime('%d.%m.%Y')}.pdf",
        )
        render.assert_called_once()
        send.assert_called_once()

    @mock.patch("acesta.user.views.user.send_message")
    @mock.patch("acesta.front.pdf.response.render_pdf")
    def test_public_offer_can_return_html_without_notification(self, render, send):
        self.client.logout()

        response = self.client.get(reverse("oferta"))
        html = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("ОФЕРТА", html)
        self.assertIn(
            "<title>Аналитический сервис ацеста. Оферта на оказание услуг</title>",
            html,
        )
        self.assertIn("/static/css/pdf_documents.css", html)
        self.assertNotIn("data:", html)
        self.assertEqual(html.count('class="pdf-document-page"'), 4)
        self.assertFalse(response.has_header("Content-Disposition"))
        render.assert_not_called()
        send.assert_not_called()

    @mock.patch("acesta.user.views.user.send_message")
    @mock.patch("acesta.front.pdf.response.render_pdf")
    def test_public_offer_query_format_does_not_control_html_url(self, render, send):
        self.client.logout()

        response = self.client.get(reverse("oferta"), {"format": "pdf"})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/html"))
        render.assert_not_called()
        send.assert_not_called()

    @mock.patch("acesta.user.views.user.send_message")
    @mock.patch("acesta.front.pdf.response.render_pdf", return_value=b"%PDF-test")
    def test_public_offer_query_format_does_not_control_pdf_url(self, render, send):
        self.client.logout()

        response = self.client.get(reverse("oferta_pdf"), {"format": "html"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        render.assert_called_once()
        send.assert_called_once()
