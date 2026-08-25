from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseBadRequest

from acesta.front.qr.generator import generate_qr


@staff_member_required
def qr_svg(request: HttpRequest) -> HttpResponse:
    try:
        caption = request.GET.get("caption")
        qr = generate_qr(
            request.GET.get("target"),
            caption=caption,
            show_caption=caption != "",
        )
    except ValueError as error:
        return HttpResponseBadRequest(str(error))

    return HttpResponse(qr.svg, content_type="image/svg+xml; charset=utf-8")
