import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import mock

from django import test
from django.conf import settings
from django.db import transaction
from django.http import Http404
from django.http import HttpRequest
from django.test import override_settings
from django.test import RequestFactory
from django.urls import path
from django.urls import reverse
from django.utils.log import AdminEmailHandler

from acesta.front.server_errors import error_page_preview
from acesta.front.server_errors import server_error
from acesta.front.utils import get_segment_market
from acesta.front.utils import get_segment_pattern


@transaction.non_atomic_requests
def controlled_server_error(request: HttpRequest):
    raise RuntimeError("Controlled server error")


urlpatterns = [path("controlled-server-error/", controlled_server_error)]
handler500 = server_error


class ServerErrorTest(test.SimpleTestCase):
    def test_server_error_template_renders_without_request_context(self):
        response = server_error(RequestFactory().get("/broken/"))

        self.assertEqual(response.status_code, 500)
        self.assertIn("Внутренняя ошибка сервера", response.content.decode())
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_server_error_selects_dashboard_page_for_authenticated_user(self):
        with TemporaryDirectory() as directory:
            templates = Path(directory) / "templates"
            (templates / "dashboard").mkdir(parents=True)
            (templates / "500.html").write_text("public", encoding="utf-8")
            (templates / "dashboard" / "500.html").write_text(
                "dashboard", encoding="utf-8"
            )
            request = RequestFactory().get("/broken/")
            request.user = SimpleNamespace(is_authenticated=True)

            with override_settings(APPS_DIR=Path(directory)):
                response = server_error(request)

        self.assertEqual(response.content, b"dashboard")

    def test_server_error_uses_fallback_when_file_cannot_be_read(self):
        request = RequestFactory().get("/broken/")
        with mock.patch("pathlib.Path.read_text", side_effect=OSError):
            response = server_error(request)

        self.assertEqual(response.status_code, 500)
        self.assertIn("Внутренняя ошибка сервера", response.content.decode())

    @override_settings(DEBUG=False, ROOT_URLCONF=__name__)
    def test_server_error_logs_original_exception_for_admin_email_handler(self):
        logger = logging.getLogger("django.request")
        handler = AdminEmailHandler()
        handler.setLevel(logging.ERROR)
        logger.addHandler(handler)
        self.client.raise_request_exception = False

        try:
            with mock.patch.object(handler, "emit") as emit:
                response = self.client.get("/controlled-server-error/")
        finally:
            logger.removeHandler(handler)

        self.assertEqual(response.status_code, 500)
        self.assertIn("Внутренняя ошибка сервера", response.content.decode())
        emit.assert_called_once()
        log_record = emit.call_args.args[0]
        self.assertIsInstance(log_record.exc_info[1], RuntimeError)
        self.assertEqual(str(log_record.exc_info[1]), "Controlled server error")


class ErrorPagePreviewTest(test.SimpleTestCase):
    @override_settings(DEBUG=True)
    def test_public_preview_has_contacts_before_sign_in(self):
        response = error_page_preview(RequestFactory().get("/preview/"))
        content = response.content.decode()

        max_position = content.index("Спросить в Max")
        telegram_position = content.index("Спросить в Telegram")
        sign_in_position = content.index("btn-outline-accent")
        self.assertLess(max_position, telegram_position)
        self.assertLess(telegram_position, sign_in_position)
        self.assertIn("/static/img/sprite.svg#logo-a", content)

    def test_preview_returns_relative_static_urls_for_both_pages(self):
        with TemporaryDirectory() as directory:
            templates = Path(directory) / "templates"
            (templates / "dashboard").mkdir(parents=True)
            (templates / "500.html").write_text(
                '<link href="/static/public.css">', encoding="utf-8"
            )
            (templates / "dashboard" / "500.html").write_text(
                '<use href="/static/img/sprite.svg#logo"></use>',
                encoding="utf-8",
            )
            for host, dashboard, asset in (
                ("localhost:8000", False, "public.css"),
                ("127.0.0.1:8765", True, "img/sprite.svg#logo"),
            ):
                with self.subTest(host=host, dashboard=dashboard):
                    request = RequestFactory().get("/preview/", HTTP_HOST=host)
                    with override_settings(
                        ALLOWED_HOSTS=["localhost", "127.0.0.1"],
                        APPS_DIR=Path(directory),
                        DEBUG=True,
                        PUBLIC_DOMAIN="acesta.ru",
                    ):
                        response = error_page_preview(request, dashboard=dashboard)

                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response["Cache-Control"], "no-store")
                    self.assertIn(f"/static/{asset}", response.content.decode())

    @override_settings(DEBUG=False)
    def test_preview_is_unavailable_without_debug(self):
        with self.assertRaises(Http404):
            error_page_preview(RequestFactory().get("/preview/"))


class FrontTest(test.TestCase):
    def test_outside_header_has_contacts_before_auth_action(self):
        response = self.client.get(reverse("help"))
        content = response.content.decode()

        max_position = content.index("Спросить в Max")
        telegram_position = content.index("Спросить в Telegram")
        auth_position = content.index("btn-outline-accent")
        self.assertLess(max_position, telegram_position)
        self.assertLess(telegram_position, auth_position)
        self.assertIn("#logo-2", content)
        self.assertIn("#logo-a", content)

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
