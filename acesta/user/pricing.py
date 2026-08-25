from dataclasses import dataclass
from decimal import Decimal
from decimal import ROUND_HALF_UP

from django.conf import settings
from django.utils import timezone

from acesta.user.models.promotion import AccessPromotion

_PROMOTION_NOT_SELECTED = object()


@dataclass(frozen=True)
class AccessPromotionSelection:
    promotion: AccessPromotion
    code: str


@dataclass(frozen=True)
class AccessPrice:
    cost: int
    period_discount: int
    period_discount_sum: int
    period_total: int
    promotion_discount: int
    promotion_discount_sum: int
    discount_sum: int
    total: int
    promotion: AccessPromotion | None
    promo_code: str


def get_active_access_promotion(segment=None):
    segment = segment or settings.DEFAULT_SEGMENT
    promotion = (
        AccessPromotion.objects.filter(
            is_active=True,
            ends_on__gte=timezone.localdate(),
        )
        .prefetch_related("codes")
        .first()
    )
    if promotion is None:
        return None

    codes = {item.segment: item.code for item in promotion.codes.all()}
    code = codes.get(segment, codes.get(settings.DEFAULT_SEGMENT, ""))
    return AccessPromotionSelection(promotion=promotion, code=code)


def calculate_access_price(
    period,
    regions=None,
    tourism_types=None,
    district=None,
    segment=None,
    promotion_selection=_PROMOTION_NOT_SELECTED,
    promotion_percent=None,
):
    from acesta.user.models import Order

    cost = Order.get_cost(period, regions, tourism_types, district)
    period_discount = int(Order.get_discount(period))
    period_total = int(
        Decimal(cost) * (Decimal(100) - Decimal(period_discount)) / Decimal(100)
    )

    if promotion_percent is None:
        if promotion_selection is _PROMOTION_NOT_SELECTED:
            promotion_selection = get_active_access_promotion(segment)
        promotion = promotion_selection.promotion if promotion_selection else None
        promotion_discount = promotion.discount if promotion else 0
        promo_code = promotion_selection.code if promotion_selection else ""
    else:
        if promotion_selection is _PROMOTION_NOT_SELECTED:
            promotion_selection = None
        promotion = promotion_selection.promotion if promotion_selection else None
        promotion_discount = int(promotion_percent)
        promo_code = promotion_selection.code if promotion_selection else ""

    total = int(
        (
            Decimal(period_total)
            * (Decimal(100) - Decimal(promotion_discount))
            / Decimal(100)
        ).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
    )
    period_discount_sum = cost - period_total
    promotion_discount_sum = period_total - total

    return AccessPrice(
        cost=cost,
        period_discount=period_discount,
        period_discount_sum=period_discount_sum,
        period_total=period_total,
        promotion_discount=promotion_discount,
        promotion_discount_sum=promotion_discount_sum,
        discount_sum=cost - total,
        total=total,
        promotion=promotion,
        promo_code=promo_code,
    )
