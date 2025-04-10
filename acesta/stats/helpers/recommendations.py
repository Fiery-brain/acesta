from django.conf import settings
from django.db.models import F
from django.db.models import Max
from django.template.defaultfilters import date as _date
from g4f import Client
from g4f.errors import RateLimitError
from g4f.errors import ResponseError
from g4f.errors import ResponseStatusError
from g4f.errors import RetryProviderError
from g4f.errors import TimeoutError

from acesta.base.decorators import append
from acesta.base.decorators import to_cache
from acesta.geo.models import City
from acesta.geo.models import Region
from acesta.geo.models import Sight
from acesta.geo.models import SightGroup
from acesta.stats.helpers.audience import get_audience
from acesta.stats.helpers.base import formatted_percentage
from acesta.stats.helpers.base import get_regions_cnt
from acesta.stats.helpers.base import round_up
from acesta.stats.helpers.interest import get_interest
from acesta.stats.helpers.rating import get_amount_rating_by_group_outstanding_places
from acesta.stats.helpers.rating import get_amount_rating_place
from acesta.stats.helpers.rating import get_interest_cities_rating
from acesta.stats.helpers.rating import get_interest_rating_place
from acesta.stats.helpers.rating import get_interest_region_rating
from acesta.stats.helpers.rating import get_interest_sight_rating
from acesta.stats.helpers.rating import get_sight_group_filter
from acesta.stats.helpers.rating import get_tourism_type_filter
from acesta.stats.helpers.sights import get_sight_stats
from acesta.stats.helpers.update_dates import get_rating_update_date


@to_cache("{key}", 60 * 60 * 24 * 14)
def _get_recommendations(question: str, **kwargs) -> str:
    """
    Returns a recommendation
    :param question: str
    :param kwargs: dict
    :return: str
    """

    # 4096 токенов = 16384 символов
    def get_ai_recommendations(question):
        client = Client()
        try:
            recommendations = (
                client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {
                            "role": "user",
                            "content": f"{question}. {settings.RECOMMENDATION_RULES}",
                        }
                    ],
                    web_search=False,
                )
                .choices[0]
                .message.content
            )

        except (
            TimeoutError,
            ResponseError,
            RateLimitError,
            ResponseStatusError,
            RetryProviderError,
            RuntimeError,
        ):
            recommendations = ""
        return recommendations

    return get_ai_recommendations(question)


def get_region_recommendations(region: Region, segment: str, data: dict) -> str:
    """
    Returns recommendations by region data
    :param region: Region
    :param segment: str
    :param data: dict
    :return: str
    """

    @append(f" {dict(settings.RECOMMENDATION_NOTE).get(segment)}")
    @append(f" Tone of voice: {dict(settings.RECOMMENDATION_TOV).get(segment)}")
    def get_question():
        return settings.REGION_RECOMMENDATION_TEMPLATE.format(
            region=region,
            sight_stats=[
                f"{item['title']} ({item['groups'].replace('<br>', ', ')}): {item['cnt']}"
                for item in get_sight_stats(code=region.code)
            ],
            interest_rating_place=get_interest_rating_place(code=region.code),
            amount_rating_place=get_amount_rating_place(code=region.code),
            outstanding_places=(
                ", ".join(
                    [
                        f"{p.get('place')} по количеству {p.get('group_title_gen')}"
                        for p in get_amount_rating_by_group_outstanding_places(
                            code=region.code
                        )
                    ]
                )
                + ". "
                if get_amount_rating_by_group_outstanding_places(code=region.code)
                else ""
            ),
            regions_cnt=get_regions_cnt(),
            segments_genitive=dict(settings.SEGMENTS_GENITIVE).get(segment),
        )

    return _get_recommendations(
        get_question(), key=f"recommendations_region_{region.code}_{segment}"
    )


def get_interest_recommendations(region: Region, segment: str, data: dict) -> str:
    """
    Returns recommendations by interest data
    :param region: Region
    :param segment: str
    :param data: dict
    :return: str
    """
    home_area, home_pk, audience_pk, tourism_type, area = (
        data.get("home_area"),
        data.get("home_pk"),
        data.get("audience_pk"),
        data.get("tourism_type"),
        data.get("area"),
    )

    interest = get_interest(region.code, home_area, area, tourism_type, home_pk or 0)

    interesants_base = interest.annotate(  #
        normalized_interest=F("ppt")
        / (interest.aggregate(max_ppt=Max("popularity_mean")).get("max_ppt") / 100)
        + F("qty") / (interest.aggregate(max_qty=Max("qty")).get("max_qty") / 100)
    ).order_by("-normalized_interest")

    if audience_pk:
        audience = [
            settings.AUDIENCE_SEGMENT_RECOMMENDATION_TEMPLATE.format(
                area_prepositional="городе"
                if area == settings.AREA_CITIES
                else "регионе",
                v_all=int(round_up(a.v_all * a.coeff, -3)),
                v_types=int(round_up(a.v_types * a.coeff, -3)),
                tourism_type=dict(settings.TOURISM_TYPES).get(a.tourism_type),
                sex=dict(settings.SEX).get(a.sex),
                age=dict(settings.AGE).get(a.age),
                v_type_sex_age=int(round_up(a.v_type_sex_age * a.coeff, -3)),
                v_sex_age_child_6=formatted_percentage(
                    a.v_sex_age_child_6, a.v_sex_age
                ),
                v_sex_age_child_7_12=formatted_percentage(
                    a.v_sex_age_child_7_12, a.v_sex_age
                ),
                v_sex_age_parents=formatted_percentage(
                    a.v_sex_age_parents, a.v_sex_age
                ),
                v_type_in_pair=formatted_percentage(a.v_type_in_pair, a.v_sex_age),
            )
            for a in get_audience(area, tourism_type, audience_pk)
        ]

    @append(f" {dict(settings.RECOMMENDATION_NOTE).get(segment)}")
    @append(f" Tone of voice {dict(settings.RECOMMENDATION_TOV).get(segment)}")
    def get_question():
        return settings.INTEREST_RECOMMENDATION_TEMPLATE.format(
            update_month=_date(get_rating_update_date(), "F Y года"),
            area_dative=(
                f"городу {City.objects.get(pk=home_pk).title}"
                if home_area == settings.AREA_CITIES
                else (
                    f"точке притяжения {Sight.objects.get(pk=home_pk)}"
                    if home_area == settings.AREA_SIGHTS
                    else f"региону {region}"
                )
            ),
            area_creative="городами" if area == settings.AREA_CITIES else "регионами",
            tourism_type=f"""{'по виду туризма ' + dict(settings.TOURISM_TYPES).get(tourism_type)
                if tourism_type else ''}""",
            selected_interesant=(
                f"""Особое внимание удели {"городу"
                if area == settings.AREA_CITIES else "региону"} {City.objects.get(pk=int(audience_pk))
            if area == settings.AREA_CITIES else Region.objects.get(pk=audience_pk)}."""
                if audience_pk
                else ""
            ),
            interesants=[
                (i.code.title, i.qty, i.ppt)
                for i in interesants_base.filter(popularity_mean__gt=100)
            ],
            not_interesants=[
                (i.code.title, i.qty, i.ppt)
                for i in interesants_base.filter(popularity_mean__lte=100)
            ],
            interesant_area_genitive_plural="городов"
            if area == settings.AREA_CITIES
            else "регионов",
            interesant_area="город" if area == settings.AREA_CITIES else "регион",
            audience=(
                settings.AUDIENCE_RECOMMENDATION_TEMPLATE.format(
                    area_prepositional="городе"
                    if area == settings.AREA_CITIES
                    else "регионе",
                    selected_interesant=(
                        City.objects.get(pk=int(audience_pk))
                        if area == settings.AREA_CITIES
                        else Region.objects.get(pk=audience_pk)
                    ),
                    audience=audience,
                )
                if audience_pk
                else ""
            ),
            regions_cnt=get_regions_cnt(),
            segments_genitive=dict(settings.SEGMENTS_GENITIVE).get(segment),
        )

    return _get_recommendations(
        get_question(),
        key=f"recommendations_interest_{region.code}_{segment}_"
        f"{home_area}_{home_pk}_{audience_pk}_{tourism_type}_{area}",
    )


def get_rating_recommendations(region: Region, segment: str, data: dict) -> str:
    """
    Returns recommendations by ratings data
    :param region: Region
    :param segment: str
    :param data: dict
    :return: str
    """
    area, tourism_type, group = (
        data.get("area"),
        data.get("tourism_type"),
        data.get("group"),
    )

    rating = (
        get_interest_cities_rating(
            get_tourism_type_filter(tourism_type),
            code=region.code,
            tourism_type=tourism_type or "",
        )
        if area == settings.AREA_CITIES
        else (
            get_interest_sight_rating(
                get_sight_group_filter(group), code=region.code, sight_group=group or ""
            )
            if area == settings.AREA_SIGHTS
            else get_interest_region_rating(
                get_tourism_type_filter(tourism_type), tourism_type=tourism_type or ""
            )
        )
    )

    @append(f" {dict(settings.RECOMMENDATION_NOTE).get(segment)}")
    @append(f" Tone of voice {dict(settings.RECOMMENDATION_TOV).get(segment)}")
    def get_question():
        return settings.RATING_RECOMMENDATION_TEMPLATE.format(
            update_month=_date(get_rating_update_date(), "F Y года"),
            area_genitive_plural=(
                "городов"
                if area == settings.AREA_CITIES
                else (
                    "точек притяжения" if area == settings.AREA_SIGHTS else "регионов"
                )
            ),
            interest_rating=[
                (
                    r.place,
                    r.home_code.title
                    if area in (settings.AREA_CITIES, settings.AREA_REGIONS)
                    else r.sight.title,
                    r.value,
                )
                for r in rating
            ],
            subject=(
                "городов"
                if area == settings.AREA_CITIES
                else "точек притяжения"
                if area == settings.AREA_SIGHTS
                else f"региона {region}"
            ),
            tourism_type=(
                f"по виду туризма {dict(settings.TOURISM_TYPES).get(tourism_type)}"
                if tourism_type
                and area in (settings.AREA_CITIES, settings.AREA_REGIONS)
                else f"{'по группе ' + SightGroup.objects.get(pk=group).title}"
                if group
                else ""
            ),
            area=(
                "город"
                if area == settings.AREA_CITIES
                else "точка притяжения"
                if area == settings.AREA_SIGHTS
                else "регион"
            ),
            regions_cnt=get_regions_cnt(),
            segments_genitive=dict(settings.SEGMENTS_GENITIVE).get(segment),
        )

    return _get_recommendations(
        get_question(),
        key=f"recommendations_rating_{region.code}_{segment}_{area}_{tourism_type}",
    )


def get_recommendations(part, region: Region, segment: str, data: dict):
    """
    Returns recommendations according to part and request data
    :param part:
    :param region:
    :param segment:
    :param data:
    :return:
    """
    if part == settings.PART_REGION:
        return get_region_recommendations(region, segment, data)
    elif part == settings.PART_INTEREST:
        return get_interest_recommendations(region, segment, data)
    elif part == settings.PART_RATING:
        return get_rating_recommendations(region, segment, data)
    else:
        raise RuntimeError(f"Unknown part {part}")
