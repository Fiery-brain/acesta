from django import template
from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from acesta.user.utils import get_request_form

register = template.Library()


@register.inclusion_tag("include/request_modal.html", takes_context=True)
def request_modal(context, subject):
    request = context.get("request")
    if request:
        user = request.user
    else:
        user = AnonymousUser()
    return dict(
        REQUEST_CONSULTATION=settings.REQUEST_CONSULTATION,
        REQUEST_CHANNELS=dict(settings.REQUEST_CHANNELS_OUTSIDE),
        consultation_form=get_request_form(user, settings.REQUEST_CONSULTATION),
        presentation_form=get_request_form(user, settings.REQUEST_PRESENTATION),
        request=request,
        subject=subject,
    )
