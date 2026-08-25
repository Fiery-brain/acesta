from django.urls import path

from acesta.front.qr.views import qr_svg

urlpatterns = [
    path("qr.svg", qr_svg, name="qr_svg"),
]
