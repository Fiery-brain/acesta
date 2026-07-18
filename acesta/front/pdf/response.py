from django.http import HttpRequest
from django.http import HttpResponse

from acesta.front.pdf.renderer import render_pdf


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
    return HttpResponse(
        render_pdf(
            html,
            profile=profile,
            base_url=request.build_absolute_uri("/"),
        ),
        content_type="application/pdf",
    )
