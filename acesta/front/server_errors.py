from pathlib import Path

from django.conf import settings
from django.http import Http404
from django.http import HttpResponse

FALLBACK_HTML = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Внутренняя ошибка сервера | ацеста</title>
</head>
<body>
<main>
<h1>Внутренняя ошибка сервера</h1>
<p>Мы уже получили сведения об этой ошибке.</p>
<p>Попробуйте загрузить страницу через некоторое время.</p>
<p><a href="/">Вернуться на главную</a></p>
</main>
</body>
</html>
"""


def _read_error_page(template_name):
    path = Path(settings.APPS_DIR) / "templates" / template_name
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return FALLBACK_HTML


def _error_response(content, status):
    response = HttpResponse(
        content,
        status=status,
        content_type="text/html; charset=utf-8",
    )
    response["Cache-Control"] = "no-store"
    return response


def server_error(request):
    """Return a pre-generated error page without rendering Django templates."""
    try:
        is_authenticated = bool(request.user.is_authenticated)
    except Exception:
        is_authenticated = False

    template_name = "dashboard/500.html" if is_authenticated else "500.html"
    return _error_response(_read_error_page(template_name), status=500)


def error_page_preview(request, dashboard=False):
    """Return a generated error page for local visual inspection."""
    if not settings.DEBUG:
        raise Http404

    template_name = "dashboard/500.html" if dashboard else "500.html"
    return _error_response(_read_error_page(template_name), status=200)
