from django import template
from django.conf import settings

register = template.Library()


@register.inclusion_tag("include/request_modal.html", takes_context=True)
def request_modal(context, *args, **kwargs):
    return dict(
        REQUEST_CONSULTATION=settings.REQUEST_CONSULTATION,
        REQUEST_CHANNELS=context["REQUEST_CHANNELS"],
        consultation_form=context["consultation_form"],
        presentation_form=context["presentation_form"],
        request=context["request"],
        subject=kwargs.get("subject"),
    )
