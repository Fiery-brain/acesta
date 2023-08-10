from django import test
from django.contrib.auth import get_user
from django.urls import reverse

from acesta.user.helpers import CredentialsMixin


class StatsTest(CredentialsMixin, test.TestCase):
    def test_responses(self):
        """
        Testing of the stats app
        :return: None
        """
        self.assertEqual(get_user(self.client).is_authenticated, False)

        # dashboard unauthorised
        response = self.client.get(reverse("region"), follow=True)
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertEqual(last_url, "/login/?next=/dashboard/")

        # interest unauthorised
        response = self.client.get(reverse("interest"), follow=True)
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertEqual(last_url, "/login/?next=/interest/")

        # rating unauthorised
        response = self.client.get(reverse("rating"), follow=True)
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertEqual(last_url, "/login/?next=/rating/")

        # rating unauthorised
        response = self.client.get(
            reverse("rating-cities", kwargs={"area": "cities"}), follow=True
        )
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertEqual(last_url, "/login/?next=/rating/cities/")

        # rating unauthorised
        response = self.client.get(
            reverse("rating-sights", kwargs={"area": "sights"}), follow=True
        )
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertEqual(last_url, "/login/?next=/rating/sights/")

        # set-region unauthorised
        response = self.client.get(
            reverse("set_region", kwargs={"code": "02"}), follow=True
        )
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertEqual(last_url, "/login/?next=/set_region/02/")

        self.client.login(**self.credentials)
        self.assertEqual(get_user(self.client).is_authenticated, True)

        # dashboard authorised
        response = self.client.get(reverse("region"))
        self.assertEqual(response.status_code, 200)

        # interest authorised
        response = self.client.get(reverse("interest"))
        self.assertEqual(response.status_code, 200)

        # rating authorised
        response = self.client.get(reverse("rating"))
        self.assertEqual(response.status_code, 200)

        # rating authorised
        response = self.client.get(reverse("rating-cities", kwargs={"area": "cities"}))
        self.assertEqual(response.status_code, 302)

        # rating authorised
        response = self.client.get(reverse("rating-sights", kwargs={"area": "sights"}))
        self.assertEqual(response.status_code, 302)

        # set-region authorised
        response = self.client.get(
            reverse("set_region", kwargs={"code": "02"}), follow=True
        )
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertEqual(last_url, "/dashboard/")
