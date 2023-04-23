from django import test
from django.contrib.auth import get_user
from django.urls import reverse

from acesta.user.helpers import CredentialsMixin
from acesta.user.models import Order


class UrlsTest(CredentialsMixin, test.TestCase):
    def test_responses(self):
        """
        Testing of the user app
        :return: None
        """
        # login unauthorised
        response = self.client.get(reverse("account_login"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(get_user(self.client).is_authenticated, False)

        # profile unauthorised
        response = self.client.get(reverse("user"), follow=True)
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertEqual(last_url, "/login/?next=/user/")

        response = self.client.post(reverse("user"), follow=True)
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertEqual(last_url, "/login/?next=/user/")

        # logout unauthorised
        response = self.client.post(reverse("account_logout"), follow=True)
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertEqual(last_url, "/")

        # costs unauthorised
        response = self.client.post(
            reverse("costs"), data={"period": 6, "regions": ["01", "02"]}, follow=True
        )
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertEqual(last_url, "/login/?next=/get_costs/")

        # order unauthorised get
        response = self.client.get(reverse("order"), follow=True)
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertEqual(last_url, "/login/?next=/new_order/")

        # order unauthorised post
        response = self.client.post(reverse("order"), follow=True)
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertEqual(last_url, "/login/?next=/new_order/")

        self.client.login(**self.credentials)
        self.assertEqual(get_user(self.client).is_authenticated, True)

        # profile authorised
        response = self.client.get(reverse("user"))
        self.assertEqual(response.status_code, 200)

        # costs authorised
        response = self.client.post(
            reverse("costs"), data={"period": 6, "regions": ["01", "02"]}
        )
        self.assertEqual(response.status_code, 200)

        # order authorised get
        response = self.client.get(reverse("order"), follow=True)
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertEqual(last_url, "/user/")

        # order authorised post without user
        response = self.client.post(
            reverse("order"),
            data={
                "period": 6,
                "regions": ["01", "02"],
            },
            follow=True,
        )
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertEqual(last_url, "/user/")
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "error")
        self.assertEqual(len(Order.objects.filter(user=get_user(self.client))), 0)

        # order authorised post with wrong region
        response = self.client.post(
            reverse("order"),
            data={
                "period": 6,
                "regions": [
                    "101",
                ],
                "user": get_user(self.client).id,
            },
            follow=True,
        )
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertEqual(last_url, "/user/")
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "error")
        self.assertEqual(len(Order.objects.filter(user=get_user(self.client))), 0)

        # order authorised post with wrong period
        response = self.client.post(
            reverse("order"),
            data={
                "period": "text",
                "regions": ["01", "02"],
                "user": get_user(self.client).id,
            },
            follow=True,
        )
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertEqual(last_url, "/user/")
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "error")
        self.assertEqual(len(Order.objects.filter(user=get_user(self.client))), 0)

        # order authorised post with right data
        response = self.client.post(
            reverse("order"),
            data={
                "period": 6,
                "regions": ["01", "02"],
                "user": get_user(self.client).id,
            },
            follow=True,
        )
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "success")
        self.assertEqual(len(Order.objects.filter(user=get_user(self.client))), 1)

        # TODO price
        response = self.client.get(reverse("price"))
        self.assertEqual(response.status_code, 200)

        # logout
        response = self.client.post(reverse("account_logout"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(get_user(self.client).is_authenticated, False)
