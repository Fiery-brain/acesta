from pathlib import Path
from unittest import mock

from django import test
from django.conf import settings
from django.template import Context
from django.template import Template
from django.urls import reverse

from acesta.front.templatetags.text import nobreak_spaces
from acesta.geo.models import Region
from acesta.user.helpers import CredentialsMixin
from acesta.user.models import AccessPromotion
from acesta.user.models import AccessPromotionCode
from acesta.user.templatetags import access_levels as access_levels_module
from acesta.user.templatetags.access_levels import access_level_table


class AccessLevelTableTest(test.TestCase):
    fixtures = ["acesta/geo/fixtures/region.yaml"]

    def setUp(self):
        self.region = Region.objects.get(code="01")

    def render_table(
        self,
        columns,
        show_actions=True,
        show_comparison=True,
        show_pricing=False,
        show_promotion_banner=True,
        show_original_prices=True,
        show_plan_explanations=True,
    ):
        template = Template(
            "{% load access_levels %}"
            "{% access_level_table region columns show_actions=show_actions "
            "show_comparison=show_comparison show_pricing=show_pricing "
            "show_promotion_banner=show_promotion_banner "
            "show_original_prices=show_original_prices "
            "show_plan_explanations=show_plan_explanations %}"
        )
        return template.render(
            Context(
                {
                    "region": self.region,
                    "columns": columns,
                    "show_actions": show_actions,
                    "show_comparison": show_comparison,
                    "show_pricing": show_pricing,
                    "show_promotion_banner": show_promotion_banner,
                    "show_original_prices": show_original_prices,
                    "show_plan_explanations": show_plan_explanations,
                }
            )
        )

    def test_renders_all_columns_in_canonical_order(self):
        html = self.render_table(["report", "basic", "full"])

        self.assertIn('data-access-level-columns="basic,full,report"', html)
        self.assertLess(
            html.index('data-access-level-heading="basic"'),
            html.index('data-access-level-heading="full"'),
        )
        self.assertLess(
            html.index('data-access-level-heading="full"'),
            html.index('data-access-level-heading="report"'),
        )
        self.assertIn(self.region.region_short, html)
        self.assertIn("Весь ЮФО", html)
        self.assertIn('aria-label="Справка: Отчёты и&nbsp;данные"', html)
        self.assertIn(
            str(
                nobreak_spaces(
                    "Готовый аналитический отчёт или данные для самостоятельного "
                    "анализа по вашему техническому заданию"
                )
            ),
            html,
        )
        self.assertNotIn("<thead>", html)
        self.assertNotIn("<tbody>", html)
        for column in (
            "service-col",
            "level-col",
            "basic-col",
            "region-col",
            "district-col",
            "report-col",
        ):
            self.assertIn(f'class="{column}"', html)
        self.assertNotRegex(html, r'<td[^>]+width="(?:18|36)%"')
        self.assertIn('rowspan="6"', html)
        self.assertEqual(html.count('data-access-level-feature-kind="simple"'), 2)
        self.assertEqual(html.count('data-access-level-feature-kind="compound"'), 4)
        self.assertEqual(html.count('class="overview" valign="middle"'), 2)
        self.assertEqual(html.count('class="detail" valign="middle"'), 2)
        for icon in (
            "region",
            "interest",
            "rating",
            "ai",
            # "api",  # Temporarily disabled with the API and widgets feature.
        ):
            self.assertIn(f"img/sprite.svg#{icon}", html)
        for tone in (
            "primary",
            "accent-primary",
            "accent-secondary",
            "ai",
            # "api",  # Temporarily disabled with the API and widgets feature.
        ):
            self.assertIn(f'class="service-icon {tone}"', html)
        self.assertNotRegex(
            html,
            r"<(?:small|b)[^>]*>\s*Оценка туристических возможностей региона",
        )
        self.assertIn('class="service" colspan="2" valign="middle"', html)
        self.assertIn('class="service" rowspan="2" valign="top"', html)
        self.assertIn('class="overview" valign="middle"', html)
        self.assertIn('class="detail" valign="middle"', html)
        self.assertIn(
            'align="center" valign="middle" '
            'data-access-level-feature-column="basic"',
            html,
        )
        self.assertIn(
            'colspan="2" align="center" valign="middle" '
            'data-access-level-feature-column="full"',
            html,
        )
        self.assertIn(
            'rowspan="6" align="center" valign="middle" '
            'data-access-level-feature-column="report"',
            html,
        )
        self.assertLess(
            html.index("Оценка туристических возможностей региона"),
            html.index("Анализ интереса потенциальных туристов"),
        )
        self.assertLess(
            html.index(
                str(nobreak_spaces("Сравнение позиций и нахождение точек роста"))
            ),
            html.index("Рекомендации искусственного интеллекта"),
        )
        # self.assertLess(
        #     html.index("Рекомендации искусственного интеллекта"),
        #     html.index(str(nobreak_spaces("API и виджеты"))),
        # )

    def test_renders_requested_column_subset(self):
        html = self.render_table(["full", "report"])

        self.assertNotIn('data-access-level-heading="basic"', html)
        self.assertNotIn('data-access-level-explanation="basic"', html)
        self.assertIn('data-access-level-explanation="full"', html)
        self.assertIn('data-access-level-explanation="report"', html)
        self.assertEqual(html.count('class="purpose '), 2)
        self.assertIn(
            'class="plan full" colspan="2" align="center" valign="middle"', html
        )
        self.assertIn('class="plan report" align="center" valign="middle"', html)
        self.assertEqual(html.count('data-access-level-feature-column="full"'), 6)
        self.assertEqual(html.count('data-access-level-feature-column="report"'), 1)

    def test_report_price_help_is_not_rendered_without_report_column(self):
        html = self.render_table(["full"])

        self.assertNotIn("Справка: Отчёты", html)

    def test_renders_plan_explanations_for_visible_columns(self):
        html = self.render_table(["basic", "full", "report"])

        self.assertIn(
            'class="spacer" colspan="2" rowspan="4" aria-hidden="true"',
            html,
        )
        self.assertNotIn("Что вы получаете", html)
        self.assertNotIn("Данные и&nbsp;инструменты", html)
        self.assertNotIn("Что вы получаете", html)
        self.assertIn("data-access-level-explanations", html)
        self.assertIn('data-access-level-explanation="basic"', html)
        self.assertIn('data-access-level-explanation="full"', html)
        self.assertIn('data-access-level-explanation="report"', html)
        self.assertEqual(html.count('class="purpose '), 3)
        self.assertIn("Для&nbsp;знакомства с&nbsp;возможностями", html)
        self.assertIn("Для&nbsp;регулярной работы с&nbsp;данными", html)
        self.assertIn("Для&nbsp;самостоятельного анализа", html)
        self.assertRegex(
            html,
            r'<td colspan="2" align="center" valign="middle"[^>]*data-access-level-explanation="full"',
        )

    def test_can_hide_plan_explanations(self):
        html = self.render_table(
            ["full", "report"],
            show_plan_explanations=False,
        )

        self.assertNotIn("data-access-level-explanation", html)
        self.assertNotIn("data-access-level-explanations", html)
        self.assertIn(
            'class="plan full" colspan="2" align="center" valign="middle"', html
        )

    def test_can_hide_all_actions(self):
        html = self.render_table(["basic", "full", "report"], show_actions=False)

        self.assertNotIn("data-access-level-action", html)
        self.assertIn("бесплатно", html)
        self.assertIn('<span class="from">от</span> 100 000 ₽', html)
        self.assertEqual(html.count('class="from"'), 3)

    def test_renders_feature_help_for_first_and_second_columns(self):
        html = self.render_table(["basic"])

        self.assertEqual(html.count("data-access-level-help"), 8)
        self.assertEqual(html.count("img/sprite.svg#help"), 8)
        self.assertIn("Справка: Оценка туристических возможностей региона", html)
        self.assertIn("Справка: Анализ интереса потенциальных туристов", html)
        self.assertIn("Справка: детальный разбор", html)
        self.assertIn("Справка: Рекомендации искусственного интеллекта", html)
        # self.assertIn(str(nobreak_spaces("Справка: API и виджеты")), html)
        self.assertIn('data-bs-toggle="tooltip"', html)
        self.assertNotRegex(html, r"<a[^>]+data-access-level-help")

    def test_dashboard_owns_tariff_styles_and_markup_stays_readable(self):
        project_root = Path(__file__).resolve().parents[3]
        css = (project_root / "acesta/static/css/dashboard.css").read_text()
        base_css = (project_root / "acesta/static/css/base.css").read_text()
        # Presentation styles are not included in the current release.
        # presentation_css = (
        #     project_root / "acesta/static/css/presentation.css"
        # ).read_text()
        offer_css = (
            project_root / "acesta/static/css/commercial_offer.css"
        ).read_text()

        self.assertNotIn(".access-level-", base_css)
        self.assertNotIn(".price-table", base_css)
        self.assertNotIn(".tariff-slide", base_css)
        self.assertNotIn(".offer-tariff", base_css)
        self.assertNotIn(".tariff-slide", css)
        self.assertNotIn(".offer-tariff", css)
        # self.assertNotIn(".price-table", presentation_css)
        # self.assertNotIn(".offer-tariff", presentation_css)
        self.assertNotIn(".price-table", offer_css)
        self.assertNotIn(".tariff-slide", offer_css)
        html = self.render_table(["full"])
        self.assertNotRegex(html, r"\baccess-level-[\w-]+__")
        self.assertNotRegex(css, r"\baccess-level-[\w-]+__")
        self.assertIn('class="service" colspan="2" valign="middle"', html)
        self.assertIn('class="service" rowspan="2" valign="top"', html)
        self.assertIn('class="overview" valign="middle"', html)
        self.assertIn('class="detail" valign="middle"', html)
        self.assertIn("d-flex align-items-start gap-2 w-100", html)
        self.assertNotIn("service-name d-inline-flex", html)
        self.assertNotIn("bg-coral", html)
        self.assertNotIn("bg-yellow-green", html)
        self.assertNotIn("bg-grey", html)
        self.assertIn(".price-table .overview{", css)
        self.assertIn(".price-table .detail{", css)
        # self.assertIn(".tariff-slide .overview", presentation_css)
        # self.assertIn(".tariff-slide .detail", presentation_css)
        self.assertIn(".offer-tariff .pdf-table", offer_css)
        self.assertIn(
            ".price-table .purpose-row td{background:transparent;border:0", css
        )
        self.assertIn("border-radius:8px;display:flex;font-weight:600", css)
        self.assertIn("height:36px;justify-content:center;width:36px", css)
        self.assertIn("background:color-mix(in srgb,var(--service-color) 7%,#fff)", css)
        self.assertIn(
            ".price-table .price .from{font-size:.7em;"
            "vertical-align:baseline;white-space:nowrap}",
            css,
        )
        self.assertIn(
            ".price-table .plan.full .price .help,.price-table .plan.report "
            ".price .help{color:inherit}",
            css,
        )
        for tone, color in (
            ("primary", "--acesta-primary"),
            ("accent-primary", "--acesta-accent-primary"),
            ("accent-secondary", "--acesta-accent-secondary"),
            ("ai", "--acesta-ai"),
            # ("api", "--acesta-api"),  # API and widgets are temporarily disabled.
        ):
            self.assertIn(
                f".price-table .service-icon.{tone}"
                f"{{--service-color:var({color})}}",
                css,
            )

    def test_does_not_render_help_for_empty_descriptions(self):
        feature_rows = (
            {
                "kind": "simple",
                "title": "Услуга",
                "description": "   ",
                "basic": True,
                "full": True,
            },
            {
                "kind": "compound",
                "title": "Составная услуга",
                "description": "",
                "levels": (
                    {
                        "title": "обзор",
                        "description": None,
                        "basic": True,
                        "full": True,
                    },
                    {
                        "title": "детальный разбор",
                        "description": "",
                        "basic": False,
                        "full": True,
                    },
                ),
            },
            {
                "kind": "simple",
                "title": "Рекомендации",
                "description": "  ",
                "basic": True,
                "full": True,
            },
        )

        with mock.patch.object(access_levels_module, "FEATURE_ROWS", feature_rows):
            html = self.render_table(["basic"])

        self.assertNotIn("data-access-level-help", html)
        self.assertNotIn("img/sprite.svg#help", html)
        self.assertIn("Услуга", html)
        self.assertIn("обзор", html)
        self.assertIn("Рекомендации", html)

    def test_rejects_unknown_feature_row_kind(self):
        feature_rows = ({"kind": "unknown", "title": "Услуга"},)

        with mock.patch.object(access_levels_module, "FEATURE_ROWS", feature_rows):
            with self.assertRaisesMessage(
                ValueError, "Unknown access level feature row kind: unknown"
            ):
                self.render_table(["basic"])

    def test_compound_feature_row_requires_two_levels(self):
        feature_rows = (
            {
                "kind": "compound",
                "title": "Услуга",
                "levels": ({"title": "Один уровень"},),
            },
        )

        with mock.patch.object(access_levels_module, "FEATURE_ROWS", feature_rows):
            with self.assertRaisesMessage(
                ValueError, "Compound access level feature rows require two levels"
            ):
                self.render_table(["basic"])

    def test_rejects_empty_and_unknown_columns(self):
        with self.assertRaisesMessage(ValueError, "At least one access level column"):
            self.render_table([])

        with self.assertRaisesMessage(
            ValueError, "Unknown access level columns: premium"
        ):
            self.render_table(["premium"])

    def test_renders_full_access_pricing(self):
        html = self.render_table(
            ["full"],
            show_actions=False,
            show_comparison=False,
            show_pricing=True,
        )

        self.assertIn('data-access-level-section="pricing"', html)
        self.assertIn('data-access-level-columns="full"', html)
        self.assertIn(self.region.title, html)
        self.assertIn("Весь ЮФО", html)
        self.assertIn("1 вид туризма", html)
        self.assertIn("все виды туризма", html)
        self.assertIn("за&nbsp;неделю", html)
        self.assertIn("за&nbsp;месяц", html)
        self.assertIn("за&nbsp;полгода", html)
        self.assertIn("за&nbsp;год", html)
        self.assertIn("со&nbsp;скидкой&nbsp;10%", html)
        self.assertIn("со&nbsp;скидкой&nbsp;20%", html)
        self.assertEqual(html.count('align="right"'), 16)

    def test_calculates_full_access_price_matrix(self):
        context = access_level_table(
            self.region,
            ["full"],
            show_actions=False,
            show_comparison=False,
            show_pricing=True,
        )

        prices = tuple(
            (
                row["region_one_tourism_type"],
                row["region_all_tourism_types"],
                row["district_one_tourism_type"],
                row["district_all_tourism_types"],
            )
            for row in context["full_access_price_rows"]
        )
        self.assertEqual(
            prices,
            (
                (2825, 10465, 13220, 48965),
                (8073, 29900, 37773, 139900),
                (43594, 161460, 203974, 755460),
                (77500, 287040, 362620, 1343040),
            ),
        )
        self.assertEqual(
            tuple(row["discount"] for row in context["full_access_price_rows"]),
            (0, 0, 10, 20),
        )

    def test_renders_monthly_promotion_in_detailed_pricing(self):
        promotion = AccessPromotion.objects.create(
            title="Акция",
            discount=30,
            is_active=True,
        )
        AccessPromotionCode.objects.create(
            promotion=promotion,
            segment=settings.DEFAULT_SEGMENT,
            code="DEFAULT030",
        )

        html = self.render_table(
            ["full"],
            show_actions=False,
            show_comparison=False,
            show_pricing=True,
        )

        self.assertIn("data-access-level-promotion", html)
        self.assertIn("Акция", html)
        self.assertIn("скидка 30%", html)
        self.assertNotIn("DEFAULT030", html)
        self.assertIn("<animateTransform", html)
        self.assertIn('stroke="currentColor"', html)
        self.assertNotIn('aria-hidden="true">%</div>', html)
        self.assertIn("<del>2\xa0825 ₽</del>", html)
        self.assertIn(">1\xa0978 ₽</strong>", html)

    def test_comparison_shows_promotion_banner_and_original_prices(self):
        AccessPromotion.objects.create(
            title="Акция",
            discount=30,
            is_active=True,
        )

        html = self.render_table(["full"], show_pricing=False)

        self.assertIn("data-access-level-promotion", html)
        self.assertIn(
            '<del class="old-price">от 2\xa0825 ₽/нед</del>',
            html,
        )
        self.assertIn('<span class="from">от</span> 1\xa0978 ₽/нед', html)
        self.assertIn('rowspan="5"', html)
        self.assertLess(
            html.index('class="old-price-row"'), html.index('class="price-row"')
        )
        self.assertLess(
            html.index('class="price-row"'), html.index('class="button-row"')
        )

    def test_comparison_without_promotion_has_no_old_price_row(self):
        html = self.render_table(["basic", "full", "report"])

        self.assertNotIn('class="old-price-row"', html)
        self.assertIn('class="price-row"', html)
        self.assertIn('class="button-row"', html)
        self.assertIn('rowspan="4"', html)

    def test_comparison_without_actions_has_no_button_row(self):
        AccessPromotion.objects.create(
            title="Акция",
            discount=30,
            is_active=True,
        )

        html = self.render_table(["full"], show_actions=False)

        self.assertIn('class="old-price-row"', html)
        self.assertIn('class="price-row"', html)
        self.assertNotIn('class="button-row"', html)
        self.assertIn('rowspan="4"', html)

    def test_can_hide_promotion_banner_without_hiding_original_prices(self):
        AccessPromotion.objects.create(
            title="Акция",
            discount=30,
            is_active=True,
        )

        html = self.render_table(
            ["full"],
            show_promotion_banner=False,
        )

        self.assertNotIn("data-access-level-promotion", html)
        self.assertIn('class="old-price"', html)
        self.assertIn('<span class="from">от</span> 1\xa0978 ₽/нед', html)

    def test_can_hide_original_prices_without_hiding_promotion_banner(self):
        AccessPromotion.objects.create(
            title="Акция",
            discount=30,
            is_active=True,
        )

        html = self.render_table(
            ["full"],
            show_original_prices=False,
        )

        self.assertIn("data-access-level-promotion", html)
        self.assertNotIn('class="old-price"', html)
        self.assertNotIn('class="old-price-row"', html)
        self.assertIn('<span class="from">от</span> 1\xa0978 ₽/нед', html)

    def test_renders_report_pricing(self):
        html = self.render_table(
            ["report"],
            show_actions=False,
            show_comparison=False,
            show_pricing=True,
        )

        self.assertIn('data-access-level-columns="report"', html)
        self.assertIn("Срок выполнения", html)
        self.assertIn("1 месяц", html)
        self.assertIn("от 100 000 ₽", html)
        self.assertNotIn("1 вид туризма", html)
        self.assertNotIn("за&nbsp;неделю", html)

    def test_rejects_invalid_pricing_columns_and_empty_sections(self):
        for columns in (["basic"], ["full", "report"]):
            with self.subTest(columns=columns):
                with self.assertRaisesMessage(
                    ValueError,
                    "Access level pricing requires exactly one full or report column",
                ):
                    self.render_table(
                        columns,
                        show_comparison=False,
                        show_pricing=True,
                    )

        with self.assertRaisesMessage(
            ValueError,
            "At least one access level table section is required",
        ):
            self.render_table(
                ["full"],
                show_comparison=False,
                show_pricing=False,
            )


class PriceAccessLevelTableTest(CredentialsMixin, test.TestCase):
    def test_price_page_uses_access_level_table_component(self):
        self.client.login(**self.credentials)

        response = self.client.get(reverse("price"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-access-level-table")
        self.assertContains(
            response,
            'data-access-level-columns="basic,full,report"',
        )
        self.assertContains(response, 'data-access-level-action="basic"')
        self.assertContains(response, self.region_title)

    def test_price_page_renders_consultation_banner_after_tariff(self):
        self.client.login(**self.credentials)

        response = self.client.get(reverse("price"))
        html = response.content.decode()

        self.assertEqual(html.count("data-price-consultation"), 1)
        self.assertLess(
            html.index("data-access-level-table"),
            html.index("data-price-consultation"),
        )
        self.assertContains(response, "Нужен индивидуальный подход?")
        self.assertContains(
            response,
            nobreak_spaces("Расскажите о ваших задачах,"),
        )
        self.assertContains(
            response,
            nobreak_spaces("а мы подготовим предложение под ваш регион и цели"),
        )
        self.assertContains(response, "Обсудить условия")
        self.assertContains(response, "sprite.svg#consultation")
        self.assertContains(response, 'data-bs-target="#individualConditions"')
        self.assertContains(
            response,
            'class="btn btn-sm btn-outline-primary text-nowrap flex-shrink-0"',
        )
        self.assertLess(
            html.index("Нужен индивидуальный подход?"),
            html.index(str(nobreak_spaces("Расскажите о ваших задачах,"))),
        )
        self.assertLess(
            html.index(str(nobreak_spaces("Расскажите о ваших задачах,"))),
            html.index("Обсудить условия"),
        )

    def test_price_page_renders_individual_conditions_modal(self):
        self.client.login(**self.credentials)

        response = self.client.get(reverse("price"))

        self.assertContains(response, 'id="individualConditions"')
        self.assertContains(response, "Индивидуальные условия")
        self.assertContains(response, "Задачи и цели")
        self.assertContains(
            response,
            'placeholder="Расскажите, какие задачи сейчас решаете"',
        )
        self.assertContains(
            response,
            nobreak_spaces(
                "Подберём условия и формат сотрудничества с учётом ваших задач и целей"
            ),
        )
        self.assertContains(response, "Отправить запрос")
        self.assertContains(
            response,
            '<input type="hidden" name="subject" value="conditions"',
        )

    def test_consultation_banner_uses_dashboard_only_styles(self):
        project_root = Path(__file__).resolve().parents[3]
        dashboard_css = (project_root / "acesta/static/css/dashboard.css").read_text()
        # Presentation styles are not included in the current release.
        # presentation_css = (
        #     project_root / "acesta/static/css/presentation.css"
        # ).read_text()
        offer_css = (
            project_root / "acesta/static/css/commercial_offer.css"
        ).read_text()

        self.assertIn(
            ".price-table .consultation-banner{",
            dashboard_css,
        )
        self.assertIn("min-height:50px;padding:6px 12px", dashboard_css)
        self.assertNotIn(".consultation-banner .btn{", dashboard_css)
        self.assertNotIn(".consultation-banner .btn:hover{", dashboard_css)
        # self.assertNotIn("consultation-banner", presentation_css)
        self.assertNotIn("consultation-banner", offer_css)

    def test_price_page_uses_bootstrap_responsive_table(self):
        project_root = Path(__file__).resolve().parents[3]
        css = (project_root / "acesta/static/css/dashboard.css").read_text()
        component_template = (
            project_root
            / "acesta/templates/user/include/access_level_table_comparison.html"
        ).read_text()
        price_template = (project_root / "acesta/templates/user/price.html").read_text()
        # Presentation template is not included in the current release.
        # presentation_template = (
        #     project_root
        #     / "acesta/templates/front/presentation/include/presentation_access_level_table.html"
        # ).read_text()
        offer_template = (
            project_root / "acesta/templates/user/pdf/offer.html"
        ).read_text()

        self.assertIn('class="tariff"', component_template)
        self.assertIn('class="table"', component_template)
        self.assertNotIn("table-responsive", component_template)
        self.assertNotIn("table-sm", component_template)
        self.assertIn('<div class="price-table">', price_template)
        self.assertIn('<div class="table-responsive">', price_template)
        self.assertLess(
            price_template.index('<div class="table-responsive">'),
            price_template.index("{% access_level_table"),
        )
        # self.assertNotIn("table-responsive", presentation_template)
        self.assertNotIn("table-responsive", offer_template)
        self.assertNotIn('class="row pb-3 overflow-auto tariff"', component_template)
        self.assertNotIn('class="col pe-0"', component_template)
        self.assertNotIn(".price-table .tariff table{table-layout:fixed}", css)
        self.assertIn(
            ".price-table .table > :not(caption) > * > *{padding:.25rem}",
            css,
        )
        self.assertIn(".price-table .service-col{width:20%}", css)
        self.assertIn(".price-table .level-col{width:16%}", css)
        self.assertIn(
            ".price-table .basic-col,.price-table .region-col,"
            ".price-table .district-col,.price-table .report-col{width:16%}",
            css,
        )
        self.assertIn(
            ".price-table .service,.price-table .overview,.price-table .detail{line-height:1.2;padding:4px 8px}",
            css,
        )
        self.assertNotRegex(
            css,
            r"\.price-table \[data-access-level-feature-column[^}]*vertical-align",
        )
        self.assertNotIn(
            'tr[data-access-level-feature-kind="compound"] .service',
            css,
        )

    def test_service_cells_use_kind_specific_vertical_alignment(self):
        project_root = Path(__file__).resolve().parents[3]
        template = (
            project_root
            / "acesta/templates/user/include/access_level_table_comparison.html"
        ).read_text()

        self.assertIn('class="service" colspan="2" valign="middle"', template)
        self.assertIn('class="service" rowspan="2" valign="top"', template)
        self.assertNotIn("align-middle", template)
        self.assertNotIn("align-top", template)
        self.assertNotIn("text-center", template)

    def test_price_page_renders_one_promotion_before_title(self):
        AccessPromotion.objects.create(
            title="Акция",
            discount=30,
            is_active=True,
        )
        self.client.login(**self.credentials)

        response = self.client.get(reverse("price"))
        html = response.content.decode()

        self.assertEqual(html.count("data-access-level-promotion"), 1)
        self.assertLess(
            html.index("data-access-level-promotion"),
            html.index('<h1 class="fs-4 mb-0 text-muted text-nowrap">'),
        )
        self.assertContains(
            response,
            'class="row promotion-row"',
        )
        self.assertContains(response, 'class="col pe-0"')
        self.assertEqual(html.count('class="waves"'), 1)
        self.assertEqual(html.count("tariff-promo-wave-gradient-back"), 2)
        self.assertEqual(html.count("tariff-promo-wave-gradient-front"), 2)
        waves_start = html.index('<svg class="waves"')
        waves_html = html[waves_start : html.index("</svg>", waves_start) + 6]
        self.assertEqual(waves_html.count("<animateTransform"), 4)
        self.assertNotIn('transform="translate(651.5 24.5)"', waves_html)
        self.assertNotIn('transform="translate(-651.5 -24.5)"', waves_html)
        self.assertIn(
            'type="scale" begin="0s" dur="28s" repeatCount="indefinite" '
            'values="1 1;1.16 1.08;1.05 1.23;1.28 1.12;1.10 .96;1.22 1.30;1 1"',
            waves_html,
        )
        self.assertIn(
            'type="scale" begin="-9s" dur="35s" repeatCount="indefinite" '
            'values="1 1;1.08 1.24;1.22 1.10;1.02 1.34;1.30 1.18;1.12 .94;1 1"',
            waves_html,
        )
        self.assertIn(
            'type="translate" additive="sum" begin="0s" dur="28s" repeatCount="indefinite" '
            'values="0 0;10 -3;-7 4;13 1;-4 -2;0 0"',
            waves_html,
        )
        self.assertIn(
            'type="translate" additive="sum" begin="-9s" dur="35s" repeatCount="indefinite" '
            'values="0 0;-8 3;6 -4;-11 1;5 4;0 0"',
            waves_html,
        )

    def test_price_page_does_not_reserve_empty_promotion_space(self):
        self.client.login(**self.credentials)

        response = self.client.get(reverse("price"))
        project_root = Path(__file__).resolve().parents[3]
        dashboard_css = (project_root / "acesta/static/css/dashboard.css").read_text()

        self.assertNotContains(response, "data-access-level-promotion")
        self.assertIn(
            ".price-table.price-heading:not(:has(.tariff-promo)){"
            "margin-bottom:1rem!important;padding-top:1.2rem}",
            dashboard_css,
        )
        self.assertIn(
            ".price-table.price-heading:not(:has(.tariff-promo)) "
            ".title-row{margin-top:0}",
            dashboard_css,
        )

    def test_promotion_uses_compact_dashboard_layout(self):
        project_root = Path(__file__).resolve().parents[3]
        base_css = (project_root / "acesta/static/css/base.css").read_text()
        dashboard_css = (project_root / "acesta/static/css/dashboard.css").read_text()
        # Presentation styles are not included in the current release.
        # presentation_css = (
        #     project_root / "acesta/static/css/presentation.css"
        # ).read_text()
        offer_css = (
            project_root / "acesta/static/css/commercial_offer.css"
        ).read_text()

        self.assertNotIn(".access-level-", base_css)
        self.assertIn("min-height:50px;padding:6px 12px", dashboard_css)
        self.assertIn(
            "height:38px;justify-content:center;width:38px",
            dashboard_css,
        )
        for css in (dashboard_css, offer_css):
            self.assertRegex(
                css,
                r"\.tariff-promo \.discount\s*\{[^}]*"
                r"color:var\(--acesta-bright-primary\)",
            )
            self.assertRegex(
                css,
                r"\.tariff-promo \.discount svg\s*\{"
                r"display:block;height:100%;width:100%\}",
            )
        self.assertNotRegex(dashboard_css, r"\baccess-level-[\w-]+__")
        self.assertIn(
            ".promotion-row:has(.tariff-promo){height:110px}",
            dashboard_css,
        )
        self.assertRegex(
            dashboard_css,
            r"\.promotion-row \.tariff-promo\{[^}]*margin:0;[^}]*width:100%",
        )
        self.assertIn(
            ".promotion-row .tariff-promo .waves{"
            "height:100%;inset:0;pointer-events:none;position:absolute;"
            "width:100%;z-index:0}",
            dashboard_css,
        )
        self.assertNotIn(
            ".tariff-promo{margin-right:12px;margin-left:12px}",
            dashboard_css,
        )

    @property
    def region_title(self):
        return Region.objects.get(code="01").region_short
