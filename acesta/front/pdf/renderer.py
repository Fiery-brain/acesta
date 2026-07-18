from dataclasses import dataclass
from typing import Mapping

from playwright.sync_api import sync_playwright

from acesta.front.pdf.resources import resolve_local_resource


@dataclass(frozen=True)
class PDFProfile:
    width: str
    height: str


PDF_PROFILES: Mapping[str, PDFProfile] = {
    "a4": PDFProfile(width="210mm", height="297mm"),
    "presentation_16_9": PDFProfile(width="13.333333in", height="7.5in"),
}


def render_pdf(
    html: str,
    profile: str = "a4",
    pdf_options: Mapping | None = None,
    base_url: str = "http://localhost/",
) -> bytes:
    """Render a complete HTML document to PDF with Chromium."""
    try:
        page_profile = PDF_PROFILES[profile]
    except KeyError as error:
        raise ValueError(f"Unknown PDF profile: {profile}") from error

    options = {
        "width": page_profile.width,
        "height": page_profile.height,
        "print_background": True,
        "prefer_css_page_size": True,
        "margin": {
            "top": "0",
            "right": "0",
            "bottom": "0",
            "left": "0",
        },
    }
    if pdf_options:
        options.update(pdf_options)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page()
            resource_errors = []

            def route_resource(route) -> None:
                try:
                    resource_path = resolve_local_resource(route.request.url)
                except (FileNotFoundError, ValueError) as error:
                    resource_errors.append(error)
                    route.abort()
                    return

                if resource_path:
                    route.fulfill(path=str(resource_path))
                else:
                    route.continue_()

            page.route("**/*", route_resource)
            if "<base " not in html:
                html = html.replace("<head>", f'<head><base href="{base_url}">', 1)
            page.set_content(html, wait_until="networkidle")
            if resource_errors:
                raise resource_errors[0]
            page.emulate_media(media="print")
            page.evaluate(
                """async () => {
                    await document.fonts.ready;
                    await Promise.all(
                        Array.from(document.images)
                            .filter((image) => !image.complete)
                            .map((image) => new Promise((resolve, reject) => {
                                image.addEventListener("load", resolve, {once: true});
                                image.addEventListener("error", reject, {once: true});
                            }))
                    );
                }"""
            )
            return page.pdf(**options)
        finally:
            browser.close()
