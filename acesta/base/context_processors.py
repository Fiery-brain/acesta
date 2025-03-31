from django.http import HttpRequest


def host(request: HttpRequest) -> dict:
    return dict(
        HOST=f"{request.scheme}://{request.META.get('HTTP_HOST')}",
    )
