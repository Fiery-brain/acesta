from pathlib import Path
from types import SimpleNamespace

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.template import engines
from django.test import RequestFactory
from django.test import SimpleTestCase

from acesta.front.context_processors import settings as front_settings
from acesta.front.templatetags.prop import get_prop
from acesta.front.templatetags.text import nobreak_spaces


class FrontContextProcessorTest(SimpleTestCase):
    def test_settings_context_contains_request_and_public_hosts(self):
        request = RequestFactory().get("/", secure=True, HTTP_HOST="example.test")
        request.user = AnonymousUser()
        context = front_settings(request)

        self.assertEqual(context["HOST"], "https://example.test")
        self.assertEqual(context["PUBLIC_DOMAIN"], settings.PUBLIC_DOMAIN)
        self.assertEqual(
            context["PUBLIC_URL"],
            f"https://{settings.PUBLIC_DOMAIN}",
        )


class FrontTemplateLibraryTest(SimpleTestCase):
    def test_get_prop_supports_dicts_and_objects(self):
        self.assertEqual(get_prop({"title": "Dictionary"}, "title"), "Dictionary")
        self.assertEqual(
            get_prop(SimpleNamespace(title="Object"), "title"),
            "Object",
        )
        self.assertEqual(get_prop({}, "missing"), "")
        self.assertEqual(get_prop(SimpleNamespace(), "missing"), "")

    def test_nobreak_spaces_preserves_non_strings_and_marks_text_safe(self):
        self.assertEqual(nobreak_spaces(42), 42)
        self.assertEqual(
            str(nobreak_spaces("текст для примера")), "текст для&nbsp;примера"
        )

    def test_all_front_template_libraries_are_loadable(self):
        template = engines["django"].from_string(
            "{% load prop qr requests text timesince %}"
            "{{ value|accusatifier|cutter }}|{{ data|get_prop:'title' }}|"
            "{{ phrase|nobreak_spaces }}"
        )

        self.assertEqual(
            template.render(
                {
                    "value": "1 неделя, 2 минуты",
                    "data": {"title": "Словарь"},
                    "phrase": "текст для примера",
                }
            ),
            "1 неделю|Словарь|текст для&nbsp;примера",
        )


class FrontTemplateConfigurationTest(SimpleTestCase):
    def test_document_templates_use_public_domain_context(self):
        template_root = Path(__file__).resolve().parents[2] / "templates"
        template_names = (
            "user/pdf/include/offer_header.html",
            "user/pdf/oferta.html",
            "include/terms_content.html",
            "include/privacy_content.html",
        )

        for template_name in template_names:
            with self.subTest(template=template_name):
                source = (template_root / template_name).read_text()
                self.assertNotIn("https://acesta.ru", source)
                self.assertNotIn("info@acesta.ru", source)
                self.assertIn("PUBLIC_", source)
