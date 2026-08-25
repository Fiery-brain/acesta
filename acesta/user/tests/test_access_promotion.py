from datetime import date
from unittest import mock

from django import test
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db import transaction
from django.urls import reverse

from acesta.user.admin import AccessPromotionCodeForm
from acesta.user.helpers import CredentialsMixin
from acesta.user.models import AccessPromotion
from acesta.user.models import AccessPromotionCode
from acesta.user.models import Order
from acesta.user.models import User
from acesta.user.pricing import calculate_access_price
from acesta.user.pricing import get_active_access_promotion


class AccessPromotionModelTest(test.TestCase):
    def test_only_one_promotion_can_be_active(self):
        AccessPromotion.objects.create(title="Первая", discount=30, is_active=True)

        with self.assertRaises(IntegrityError), transaction.atomic():
            AccessPromotion.objects.create(title="Вторая", discount=35, is_active=True)

    def test_discount_must_be_between_one_and_ninety_nine(self):
        for discount in (0, 100):
            with self.subTest(discount=discount):
                promotion = AccessPromotion(title="Акция", discount=discount)
                with self.assertRaisesMessage(
                    ValidationError,
                    "Убедитесь, что это значение",
                ):
                    promotion.full_clean()

    def test_segment_code_is_unique_inside_promotion(self):
        promotion = AccessPromotion.objects.create(title="Акция", discount=30)
        AccessPromotionCode.objects.create(
            promotion=promotion,
            segment=settings.DEFAULT_SEGMENT,
            code="DEFAULT030",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            AccessPromotionCode.objects.create(
                promotion=promotion,
                segment=settings.DEFAULT_SEGMENT,
                code="SECOND0030",
            )

    def test_segment_code_is_normalized_to_uppercase(self):
        promotion = AccessPromotion.objects.create(title="Акция", discount=30)

        promotion_code = AccessPromotionCode.objects.create(
            promotion=promotion,
            segment=settings.DEFAULT_SEGMENT,
            code="winter2026",
        )

        self.assertEqual(promotion_code.code, "WINTER2026")

    def test_admin_form_normalizes_segment_code_to_uppercase(self):
        promotion = AccessPromotion.objects.create(title="Акция", discount=30)
        form = AccessPromotionCodeForm(
            data={
                "promotion": promotion.pk,
                "segment": settings.DEFAULT_SEGMENT,
                "code": "winter2026",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["code"], "WINTER2026")

    def test_segment_code_must_contain_ten_latin_letters_and_digits(self):
        promotion = AccessPromotion.objects.create(title="Акция", discount=30)

        for code in (
            "ABC123456",
            "ABC12345678",
            "ЗИМА202600",
            "WINTER-026",
            "WINTER 026",
        ):
            with self.subTest(code=code):
                promotion_code = AccessPromotionCode(
                    promotion=promotion,
                    segment=settings.DEFAULT_SEGMENT,
                    code=code,
                )
                with self.assertRaisesMessage(
                    ValidationError,
                    "Промокод должен состоять ровно из 10 латинских букв и цифр",
                ):
                    promotion_code.full_clean()


class AccessPromotionSelectionTest(test.TestCase):
    def setUp(self):
        self.promotion = AccessPromotion.objects.create(
            title="До конца месяца",
            discount=30,
            is_active=True,
        )
        AccessPromotionCode.objects.create(
            promotion=self.promotion,
            segment=settings.DEFAULT_SEGMENT,
            code="DEFAULT030",
        )
        AccessPromotionCode.objects.create(
            promotion=self.promotion,
            segment=settings.SEGMENT_GOVERNMENT,
            code="GOVERN0030",
        )

    def test_uses_exact_segment_code(self):
        selection = get_active_access_promotion(settings.SEGMENT_GOVERNMENT)

        self.assertEqual(selection.code, "GOVERN0030")

    def test_falls_back_to_default_segment_code(self):
        selection = get_active_access_promotion(settings.SEGMENT_TIC)

        self.assertEqual(selection.code, "DEFAULT030")

    def test_discount_works_without_fallback_code(self):
        self.promotion.codes.all().delete()

        selection = get_active_access_promotion(settings.SEGMENT_TIC)

        self.assertEqual(selection.promotion, self.promotion)
        self.assertEqual(selection.code, "")

    @mock.patch("acesta.user.models.promotion.timezone.localdate")
    def test_save_sets_deadline_to_last_day_of_month(self, localdate):
        localdate.return_value = date(2026, 8, 25)
        self.promotion.save()

        self.promotion.refresh_from_db()

        self.assertEqual(self.promotion.ends_on, date(2026, 8, 31))

    def test_expired_promotion_is_not_selected(self):
        AccessPromotion.objects.filter(pk=self.promotion.pk).update(
            ends_on=date(2026, 8, 31),
        )

        with mock.patch(
            "acesta.user.pricing.timezone.localdate", return_value=date(2026, 9, 1)
        ):
            self.assertIsNone(get_active_access_promotion())

    def test_saving_expired_promotion_renews_it_for_current_month(self):
        AccessPromotion.objects.filter(pk=self.promotion.pk).update(
            ends_on=date(2026, 8, 31),
        )

        with mock.patch(
            "acesta.user.models.promotion.timezone.localdate",
            return_value=date(2026, 9, 1),
        ):
            self.promotion.save()

        self.promotion.refresh_from_db()

        with mock.patch(
            "acesta.user.pricing.timezone.localdate", return_value=date(2026, 9, 1)
        ):
            self.assertEqual(get_active_access_promotion().promotion, self.promotion)
        self.assertEqual(self.promotion.ends_on, date(2026, 9, 30))


class AccessPriceTest(test.TestCase):
    fixtures = ["acesta/geo/fixtures/region.yaml"]

    def setUp(self):
        self.promotion = AccessPromotion.objects.create(
            title="Акция",
            discount=30,
            is_active=True,
        )

    def test_applies_period_discount_then_promotion(self):
        price = calculate_access_price(
            6,
            ["01"],
            [settings.TOURISM_TYPE_DEFAULT],
        )

        self.assertEqual(price.cost, 48438)
        self.assertEqual(price.period_discount, 10)
        self.assertEqual(price.period_total, 43594)
        self.assertEqual(price.promotion_discount, 30)
        self.assertEqual(price.promotion_discount_sum, 13078)
        self.assertEqual(price.total, 30516)
        self.assertEqual(price.discount_sum, 17922)

    @mock.patch("acesta.user.models.Order.get_discount", return_value=0)
    @mock.patch("acesta.user.models.Order.get_cost", return_value=1001)
    def test_promotion_uses_round_half_up(self, get_cost, get_discount):
        for promotion_percent, expected in ((60, 400), (50, 501), (40, 601)):
            with self.subTest(promotion_percent=promotion_percent):
                price = calculate_access_price(
                    1,
                    promotion_percent=promotion_percent,
                )
                self.assertEqual(price.total, expected)


class AccessPromotionOrderTest(CredentialsMixin, test.TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.get(username=self.credentials["email"])
        self.user.segment = settings.SEGMENT_GOVERNMENT
        self.user.save(update_fields=["segment"])
        self.promotion = AccessPromotion.objects.create(
            title="Акция",
            discount=30,
            is_active=True,
        )
        AccessPromotionCode.objects.create(
            promotion=self.promotion,
            segment=settings.SEGMENT_GOVERNMENT,
            code="GOVERN0030",
        )
        self.client.login(**self.credentials)

    def _order_data(self, promo="GOVERN0030"):
        return {
            "user": self.user.pk,
            "period": 6,
            "regions": ["01"],
            "tourism_types": [settings.TOURISM_TYPE_DEFAULT],
            "promo": promo,
        }

    def test_ajax_and_saved_order_use_same_price(self):
        costs = self.client.post(reverse("costs"), self._order_data()).json()
        self.client.post(reverse("order"), self._order_data())
        order = Order.objects.get()

        self.assertEqual(int(order.cost), costs["cost"])
        self.assertEqual(int(order.discount), costs["discount_sum"])
        self.assertEqual(int(order.promotion_discount), costs["promotion_discount_sum"])
        self.assertEqual(int(order.total), costs["total"])
        self.assertEqual(order.promotion, self.promotion)
        self.assertEqual(order.promotion_percent, 30)
        self.assertEqual(order.promo, "GOVERN0030")

    def test_user_can_replace_decorative_code_without_changing_price(self):
        costs = self.client.post(reverse("costs"), self._order_data()).json()
        self.client.post(reverse("order"), self._order_data(promo="MYCODE"))
        order = Order.objects.get()

        self.assertEqual(order.promo, "MYCODE")
        self.assertEqual(int(order.total), costs["total"])

    def test_order_snapshot_does_not_use_changed_promotion(self):
        self.client.post(reverse("order"), self._order_data())
        order = Order.objects.get()
        original_total = order.total
        self.promotion.discount = 50
        self.promotion.is_active = False
        self.promotion.save(update_fields=["discount", "is_active"])

        order.inn = "1234567890"
        order.save()
        order.refresh_from_db()

        self.assertEqual(order.promotion_percent, 30)
        self.assertEqual(order.total, original_total)

    def test_order_form_is_prefilled_with_segment_code(self):
        response = self.client.get(reverse("user"))

        self.assertContains(response, 'value="GOVERN0030"')
