from django.template import Context
from django.template import Template
from django.test import SimpleTestCase


class InlineOfferSvgTagTest(SimpleTestCase):
    def test_inlines_animated_static_svg(self):
        html = Template("{% load text %}{% inline_offer_svg %}").render(Context())

        self.assertIn("<svg", html)
        self.assertIn("<animateTransform", html)
        self.assertIn('fill="currentColor"', html)
