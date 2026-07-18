from unittest import mock

from dateutil.relativedelta import relativedelta
from django import test
from django.conf import settings
from django.contrib.auth import get_user
from django.urls import reverse
from django.utils.timezone import now

from acesta.geo.models import Region
from acesta.geo.models import Sight
from acesta.user import format_date
from acesta.user import get_date
from acesta.user.helpers import CredentialsMixin
from acesta.user.models import Order
from acesta.user.models import Support


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

        # price unauthorised
        response = self.client.get(reverse("price"), follow=True)
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertEqual(last_url, "/login/?next=/price/")

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
                "period": 0.12,
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
                "period": 6.0,
                "regions": ["01", "02"],
                "user": get_user(self.client).id,
            },
            follow=True,
        )
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "success")
        self.assertEqual(len(Order.objects.filter(user=get_user(self.client))), 1)

        # price authorised
        response = self.client.get(reverse("price"))
        self.assertEqual(response.status_code, 200)

        # logout
        response = self.client.post(reverse("account_logout"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(get_user(self.client).is_authenticated, False)

    def test_orders(self):
        self.assertGreater(len(settings.TOURISM_TYPES), 0)

        self.client.login(**self.credentials)
        self.assertEqual(get_user(self.client).is_authenticated, True)

        user = get_user(self.client)

        # simple order
        o = Order.objects.create(period=0.25, user=user)
        o.regions.add(Region.objects.get(code="01"))

        self.assertEqual(len(user.regions.all()), 0)
        self.assertEqual(user.period_info, {})
        self.assertIsNone(user.tourism_types)

        o.state = settings.STATE_DONE
        o.save()

        period_info = user.period_info

        self.assertEqual(len(user.regions.all()), 1)
        self.assertIn("01", period_info.keys())
        self.assertIsNone(user.tourism_types)

        self.assertEqual(
            get_date(period_info.get("01").get("start")), get_date(format_date(now()))
        )

        self.assertEqual(
            get_date(period_info.get("01").get("end")),
            get_date(format_date(now() + relativedelta(days=7))),
        )

        # done order
        o = Order.objects.create(
            period=0.5,
            user=user,
            state=settings.STATE_DONE,
            tourism_types=["spa", "museum"],
        )
        o.regions.add(Region.objects.get(code="02"))

        period_info = user.period_info

        self.assertEqual(len(user.regions.all()), 2)
        self.assertIn("02", period_info.keys())
        self.assertSetEqual(set(user.tourism_types), {"spa", "museum"})

        self.assertEqual(
            get_date(period_info.get("02").get("start")), get_date(format_date(now()))
        )

        self.assertEqual(
            get_date(period_info.get("02").get("end")),
            get_date(format_date(now() + relativedelta(days=14))),
        )

        # clearing subscription
        period_info["01"]["end"] = format_date(now() - relativedelta(days=1))

        user.period_info = period_info
        user.save()

        self.assertEqual(user.period_info["01"]["end"], period_info["01"]["end"])

        user.clean_up_old_periods()

        self.assertEqual(len(user.regions.all()), 1)
        self.assertEqual(len(user.period_info), 1)
        self.assertIn("02", period_info.keys())
        self.assertSetEqual(set(user.tourism_types), {"spa", "museum"})

        period_info["02"]["end"] = format_date(now() - relativedelta(days=1))

        user.period_info = period_info
        user.save()

        user.clean_up_old_periods()

        self.assertEqual(len(user.regions.all()), 0)
        self.assertEqual(user.period_info, {})
        self.assertIsNone(user.tourism_types)


class SightChangeSupportTest(CredentialsMixin, test.TestCase):
    def setUp(self):
        super().setUp()
        self.client.login(**self.credentials)
        self.user = get_user(self.client)
        self.sight = Sight.objects.create(
            code=self.user.current_region,
            title="Тестовая точка",
            is_pub=True,
        )

    @mock.patch("acesta.user.views.communications.send_message")
    def test_sight_change_saves_structured_message_and_sends_email(self, send_message):
        response = self.client.post(
            reverse("support"),
            {
                "subject": settings.SUPPORT_SIGHTS,
                "sight_id": self.sight.pk,
                "message": "Уточнить адрес",
            },
            HTTP_REFERER=reverse("region"),
        )

        self.assertEqual(response.status_code, 302)
        support_message = Support.objects.get()
        self.assertEqual(support_message.user, self.user)
        self.assertEqual(
            support_message.message,
            (
                f"ID точки притяжения: {self.sight.pk}\n"
                "Название: Тестовая точка\n"
                "Предлагаемые изменения:\nУточнить адрес"
            ),
        )
        send_message.assert_called_once_with(
            "Редактирование точек притяжения",
            support_message.message,
        )

    @mock.patch("acesta.user.views.communications.send_message")
    def test_sight_change_rejects_sight_from_another_region(self, send_message):
        other_region = Region.objects.exclude(pk=self.user.current_region_id).first()
        other_sight = Sight.objects.create(
            code=other_region,
            title="Чужая точка",
            is_pub=True,
        )

        response = self.client.post(
            reverse("support"),
            {
                "subject": settings.SUPPORT_SIGHTS,
                "sight_id": other_sight.pk,
                "message": "Подменённая точка",
            },
            HTTP_REFERER=reverse("region"),
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Support.objects.exists())
        send_message.assert_called_once()
        self.assertIn("Ошибка при добавлении сообщения", send_message.call_args.args[0])

    @mock.patch("acesta.user.views.communications.send_message")
    def test_sight_change_rejects_empty_suggestion(self, send_message):
        response = self.client.post(
            reverse("support"),
            {
                "subject": settings.SUPPORT_SIGHTS,
                "sight_id": self.sight.pk,
                "message": "   ",
            },
            HTTP_REFERER=reverse("region"),
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Support.objects.exists())
        send_message.assert_called_once()

    @mock.patch("acesta.user.views.communications.send_message")
    def test_new_sight_request_keeps_description(self, send_message):
        response = self.client.post(
            reverse("support"),
            {
                "subject": settings.SUPPORT_SIGHTS,
                "message": "Добавить новую точку",
            },
            HTTP_REFERER=reverse("region"),
        )

        self.assertEqual(response.status_code, 302)
        support_message = Support.objects.get()
        self.assertEqual(support_message.message, "Добавить новую точку")
        send_message.assert_called_once_with(
            "Редактирование точек притяжения",
            "Добавить новую точку",
        )
