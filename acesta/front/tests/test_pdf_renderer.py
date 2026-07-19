import tempfile
from pathlib import Path
from unittest import mock

from django.test import RequestFactory
from django.test import SimpleTestCase

from acesta.front.pdf.renderer import render_pdf
from acesta.front.pdf.resources import resolve_local_resource
from acesta.front.pdf.response import document_response


class PDFRendererTest(SimpleTestCase):
    @mock.patch("acesta.front.pdf.renderer.sync_playwright")
    def test_renderer_waits_for_assets_and_closes_browser(self, sync_playwright):
        manager = sync_playwright.return_value
        playwright = manager.__enter__.return_value
        browser = playwright.chromium.launch.return_value
        page = browser.new_page.return_value
        page.pdf.return_value = b"%PDF-rendered"

        result = render_pdf(
            "<html><head></head><body>Test</body></html>",
            base_url="https://example.test/",
        )

        self.assertEqual(result, b"%PDF-rendered")
        page.set_content.assert_called_once_with(
            '<html><head><base href="https://example.test/"></head>'
            "<body>Test</body></html>",
            wait_until="networkidle",
        )
        page.route.assert_called_once()
        page.emulate_media.assert_called_once_with(media="print")
        page.evaluate.assert_called_once()
        self.assertEqual(page.pdf.call_args.kwargs["width"], "210mm")
        self.assertEqual(page.pdf.call_args.kwargs["height"], "297mm")
        browser.close.assert_called_once()

    def test_renderer_rejects_unknown_profile(self):
        with self.assertRaisesMessage(ValueError, "Unknown PDF profile"):
            render_pdf("<html></html>", profile="letter")

    def test_static_resource_is_resolved_by_django_finders(self):
        path = resolve_local_resource(
            "https://example.test/static/css/pdf_documents.css"
        )

        self.assertTrue(path.is_file())
        self.assertEqual(path.name, "pdf_documents.css")

    def test_static_finder_takes_priority_over_collected_copy(self):
        with tempfile.TemporaryDirectory() as static_root:
            collected_asset = Path(static_root) / "img" / "logo.png"
            collected_asset.parent.mkdir()
            collected_asset.write_bytes(b"old")
            source_asset = Path(static_root) / "source" / "logo.png"
            source_asset.parent.mkdir()
            source_asset.write_bytes(b"current")

            with self.settings(STATIC_ROOT=static_root), mock.patch(
                "acesta.front.pdf.resources.finders.find",
                return_value=str(source_asset),
            ):
                resolved = resolve_local_resource(
                    "https://example.test/static/img/logo.png"
                )

        self.assertEqual(resolved, source_asset)

    def test_collected_static_resource_is_resolved_from_static_root(self):
        with tempfile.TemporaryDirectory() as static_root:
            asset = Path(static_root) / "css" / "pdf_documents.badb093c9377.css"
            asset.parent.mkdir()
            asset.write_text("body { color: black; }")

            with self.settings(STATIC_ROOT=static_root):
                resolved = resolve_local_resource(
                    "https://example.test/static/" "css/pdf_documents.badb093c9377.css"
                )

        self.assertEqual(resolved, asset.resolve())

    def test_unknown_static_resource_has_clear_error(self):
        with self.assertRaisesMessage(
            FileNotFoundError,
            "Static resource not found: /static/missing.png",
        ):
            resolve_local_resource("https://example.test/static/missing.png")

    def test_static_resource_rejects_path_traversal(self):
        with self.assertRaisesMessage(ValueError, "Unsafe static resource path"):
            resolve_local_resource(
                "https://example.test/static/%2e%2e/config/settings/base.py"
            )

    def test_media_resource_is_restricted_to_media_root(self):
        with tempfile.TemporaryDirectory() as media_root:
            asset = Path(media_root) / "presentation" / "photo.jpg"
            asset.parent.mkdir()
            asset.write_bytes(b"image")

            with self.settings(MEDIA_ROOT=media_root):
                resolved = resolve_local_resource(
                    "https://example.test/media/presentation/photo.jpg"
                )
                self.assertEqual(resolved, asset.resolve())

                with self.assertRaisesMessage(ValueError, "Unsafe media resource path"):
                    resolve_local_resource(
                        "https://example.test/media/%2e%2e/private.txt"
                    )


class DocumentResponseTest(SimpleTestCase):
    @mock.patch("acesta.front.pdf.response.render_pdf", return_value=b"%PDF-test")
    def test_document_without_filename_does_not_set_disposition(self, render):
        request = RequestFactory().get("/presentation/")

        response = document_response(
            request,
            "<html><head><title>Presentation</title></head></html>",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.has_header("Content-Disposition"))
        render.assert_called_once()
