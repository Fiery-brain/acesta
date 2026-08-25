from django import template
from django.conf import settings

from acesta.user.apps import DISCOUNTS
from acesta.user.apps import PRICES
from acesta.user.pricing import calculate_access_price
from acesta.user.pricing import get_active_access_promotion

register = template.Library()

ACCESS_LEVEL_COLUMN_ORDER = ("basic", "full", "report")

ACCESS_LEVEL_PLAN_EXPLANATIONS = {
    "basic": "Для знакомства с возможностями",
    "full": "Для регулярной работы с данными с полной детализацией",
    "report": "Для самостоятельного анализа",
}

FULL_ACCESS_PERIODS = (
    (0.25, "за неделю"),
    (1, "за месяц"),
    (6, "за полгода"),
    (12, "за год"),
)
#  Обзор Детальный разбор
FEATURE_KIND_SIMPLE = "simple"
FEATURE_KIND_COMPOUND = "compound"

FEATURE_ROWS = (
    {
        "kind": FEATURE_KIND_SIMPLE,
        "icon": "region",
        "tone": "primary",
        "title": "Оценка туристических возможностей региона",
        "description": (
            "Показывает туристическую специализацию региона, его позиции и известные "
            "точки притяжения. Позволяет дополнять и актуализировать точки притяжения "
            "регионального уровня."
        ),
        "basic": True,
        "full": True,
    },
    {
        "kind": FEATURE_KIND_COMPOUND,
        "icon": "interest",
        "tone": "accent-primary",
        "title": "Анализ интереса потенциальных туристов",
        "description": (
            "Даёт возможность отслеживать динамику и географию интереса, видеть тренды, "
            "состав целевых групп и изменения интереса во времени."
        ),
        "levels": (
            {
                "title": "обзор",
                "description": (
                    "Позволяет видеть интерес к турпродуктам и состав целевых групп на "
                    "уровне регионов, оценивать текущую ситуацию и её динамику."
                ),
                "variant": "overview",
                "basic": True,
                "full": True,
            },
            {
                "title": "детальный разбор",
                "description": (
                    "Расширяет анализ до городов и точек притяжения и помогает подробнее "
                    "видеть географию интереса и состав целевых групп."
                ),
                "variant": "detail",
                "basic": False,
                "full": True,
            },
        ),
    },
    {
        "kind": FEATURE_KIND_COMPOUND,
        "icon": "rating",
        "tone": "accent-secondary",
        "title": "Сравнение позиций и нахождение точек роста",
        "description": (
            "Помогает сравнивать территории по туристическому потенциалу и популярности "
            "отдельных видов туризма, видеть изменение позиций и тренды и находить точки "
            "роста."
        ),
        "levels": (
            {
                "title": "обзор",
                "description": (
                    "Даёт возможность сравнивать регионы по туристическому потенциалу и "
                    "уровню интереса, видеть общие позиции, динамику и тренды, а также "
                    "сравнивать позиции по различным видам туризма."
                ),
                "variant": "overview",
                "basic": True,
                "full": True,
            },
            {
                "title": "детальный разбор",
                "description": (
                    "Расширяет сравнение до городов и точек притяжения: позволяет видеть "
                    "их общие позиции, динамику и тренды, сравнивать позиции по различным "
                    "видам туризма и находить точки роста."
                ),
                "variant": "detail",
                "basic": False,
                "full": True,
            },
        ),
    },
    {
        "kind": FEATURE_KIND_SIMPLE,
        "icon": "ai",
        "tone": "ai",
        "title": "Рекомендации искусственного интеллекта",
        "description": (
            "Помогают получить конкретные рекомендации для решения текущих задач. Агент "
            "искусственного интеллекта учитывает специфику задач вашей профессиональной "
            "специализации, особенности территории и актуальные данные сервиса."
        ),
        "basic": True,
        "full": True,
    },
    # {
    #     "kind": FEATURE_KIND_SIMPLE,
    #     "icon": "api",
    #     "tone": "api",
    #     "title": "API и виджеты",
    #     "description": (
    #         "API для обмена данными и интеграции с вашими сервисами, готовые виджеты для размещения на вашем сайте."
    #     ),
    #     "basic": True,
    #     "full": True,
    # },
)


def _clean_description(value):
    return value.strip() if isinstance(value, str) else ""


def _get_feature_rows():
    rows = []
    for row in FEATURE_ROWS:
        kind = row.get("kind")
        if kind not in (FEATURE_KIND_SIMPLE, FEATURE_KIND_COMPOUND):
            raise ValueError(f"Unknown access level feature row kind: {kind}")

        normalized_row = {
            **row,
            "description": _clean_description(row.get("description")),
        }
        if kind == FEATURE_KIND_COMPOUND:
            levels = row.get("levels", ())
            if len(levels) != 2:
                raise ValueError(
                    "Compound access level feature rows require two levels"
                )
            normalized_row["levels"] = tuple(
                {
                    **level,
                    "description": _clean_description(level.get("description")),
                }
                for level in levels
            )
        rows.append(normalized_row)
    return tuple(rows)


def _get_feature_row_count(feature_rows):
    return sum(2 if row["kind"] == FEATURE_KIND_COMPOUND else 1 for row in feature_rows)


def _get_columns(columns):
    if isinstance(columns, str):
        raise ValueError("Access level columns must be passed as an array")

    try:
        requested_columns = set(columns)
    except TypeError as error:
        raise ValueError("Access level columns must be passed as an array") from error

    if not requested_columns:
        raise ValueError("At least one access level column is required")

    unknown_columns = requested_columns.difference(ACCESS_LEVEL_COLUMN_ORDER)
    if unknown_columns:
        unknown = ", ".join(sorted(map(str, unknown_columns)))
        raise ValueError(f"Unknown access level columns: {unknown}")

    return tuple(
        column for column in ACCESS_LEVEL_COLUMN_ORDER if column in requested_columns
    )


def _get_access_price(
    period,
    regions=None,
    tourism_types=None,
    district=None,
    segment=None,
    promotion_selection=None,
):
    return calculate_access_price(
        period,
        regions,
        tourism_types,
        district,
        segment=segment,
        promotion_selection=promotion_selection,
    )


def _get_full_access_price_rows(region, segment, promotion_selection):
    district = region.federal_district
    regions = [region.code]
    tourism_types = [settings.TOURISM_TYPE_DEFAULT]

    rows = []
    for period, label in FULL_ACCESS_PERIODS:
        prices = {
            "region_one_tourism_type": _get_access_price(
                period,
                regions,
                tourism_types,
                segment=segment,
                promotion_selection=promotion_selection,
            ),
            "region_all_tourism_types": _get_access_price(
                period,
                regions,
                segment=segment,
                promotion_selection=promotion_selection,
            ),
            "district_one_tourism_type": _get_access_price(
                period,
                None,
                tourism_types,
                district,
                segment=segment,
                promotion_selection=promotion_selection,
            ),
            "district_all_tourism_types": _get_access_price(
                period,
                None,
                None,
                district,
                segment=segment,
                promotion_selection=promotion_selection,
            ),
        }
        row = {
            "label": label,
            "discount": next(iter(prices.values())).period_discount,
        }
        for name, price in prices.items():
            row[name] = price.total
            row[f"{name}_original"] = price.period_total
        rows.append(row)
    return tuple(rows)


def _validate_sections(columns, show_comparison, show_pricing):
    if not show_comparison and not show_pricing:
        raise ValueError("At least one access level table section is required")

    if show_pricing and columns not in (("full",), ("report",)):
        raise ValueError(
            "Access level pricing requires exactly one full or report column"
        )


def _get_promotion_context(segment=None):
    segment = segment or settings.DEFAULT_SEGMENT
    promotion_selection = get_active_access_promotion(segment)
    return promotion_selection, {
        "promotion": promotion_selection.promotion if promotion_selection else None,
        "promotion_deadline": (
            promotion_selection.promotion.ends_on if promotion_selection else None
        ),
    }


@register.inclusion_tag("user/include/access_level_table_promotion.html")
def access_promotion_banner(segment=None):
    _, context = _get_promotion_context(segment)
    context["show_animated_waves"] = True
    return context


@register.inclusion_tag("user/include/access_level_table.html")
def access_level_table(
    region,
    columns,
    show_actions=True,
    show_comparison=True,
    show_pricing=False,
    segment=None,
    show_promotion_banner=True,
    show_original_prices=True,
    show_plan_explanations=True,
    use_pdf_icons=False,
    show_animated_waves=False,
):
    columns = _get_columns(columns)
    _validate_sections(columns, show_comparison, show_pricing)
    district = region.federal_district
    segment = segment or settings.DEFAULT_SEGMENT
    promotion_selection, promotion_context = _get_promotion_context(segment)
    show_full = "full" in columns
    full_access_price_rows = (
        _get_full_access_price_rows(region, segment, promotion_selection)
        if show_pricing and show_full
        else ()
    )

    if show_comparison and show_full:
        if full_access_price_rows:
            price_region = full_access_price_rows[0]["region_one_tourism_type"]
            price_district = full_access_price_rows[0]["district_one_tourism_type"]
            price_region_original = full_access_price_rows[0][
                "region_one_tourism_type_original"
            ]
            price_district_original = full_access_price_rows[0][
                "district_one_tourism_type_original"
            ]
        else:
            tourism_types = [settings.TOURISM_TYPE_DEFAULT]
            region_price = _get_access_price(
                0.25,
                [region.code],
                tourism_types,
                segment=segment,
                promotion_selection=promotion_selection,
            )
            district_price = _get_access_price(
                0.25,
                None,
                tourism_types,
                district,
                segment=segment,
                promotion_selection=promotion_selection,
            )
            price_region = region_price.total
            price_district = district_price.total
            price_region_original = region_price.period_total
            price_district_original = district_price.period_total
    else:
        price_region = None
        price_district = None
        price_region_original = None
        price_district_original = None

    feature_rows = _get_feature_rows()

    return {
        "columns": columns,
        "show_basic": "basic" in columns,
        "show_full": show_full,
        "show_report": "report" in columns,
        "first_column": columns[0],
        "last_column": columns[-1],
        "show_actions": show_actions,
        "show_comparison": show_comparison,
        "show_pricing": show_pricing,
        "region": region,
        "district_label": f"Весь {district}",
        "price_region": price_region,
        "price_district": price_district,
        "price_region_original": price_region_original,
        "price_district_original": price_district_original,
        "full_access_price_rows": full_access_price_rows,
        "prices": PRICES,
        "discounts": DISCOUNTS,
        "feature_rows": feature_rows,
        "feature_row_count": _get_feature_row_count(feature_rows),
        **promotion_context,
        "show_promotion_banner": show_promotion_banner,
        "show_original_prices": show_original_prices,
        "comparison_header_rowspan": 3
        + int(bool(promotion_selection and show_original_prices))
        + int(bool(show_actions)),
        "show_plan_explanations": show_plan_explanations,
        "use_pdf_icons": use_pdf_icons,
        "show_animated_waves": show_animated_waves,
        "plan_explanations": ACCESS_LEVEL_PLAN_EXPLANATIONS,
    }
