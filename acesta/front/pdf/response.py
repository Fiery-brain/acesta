from html.parser import HTMLParser

from django.http import HttpRequest
from django.http import HttpResponse
from django.utils.http import content_disposition_header

from acesta.front.pdf.renderer import render_pdf


class _DocumentMetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.filename = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "meta" and attributes.get("name") == "pdf-filename":
            self.filename = (attributes.get("content") or "").strip()


def document_response(
    request: HttpRequest,
    html: str,
    profile: str = "a4",
) -> HttpResponse:
    output_format = request.GET.get("format", "pdf")
    if output_format == "html":
        return HttpResponse(html, content_type="text/html; charset=utf-8")
    if output_format != "pdf":
        return HttpResponse("Unsupported document format", status=400)

    response = HttpResponse(
        render_pdf(
            html,
            profile=profile,
            base_url=request.build_absolute_uri("/"),
        ),
        content_type="application/pdf",
    )
    parser = _DocumentMetadataParser()
    parser.feed(html)
    if parser.filename:
        response["Content-Disposition"] = content_disposition_header(
            as_attachment=False,
            filename=parser.filename,
        )
    return response
