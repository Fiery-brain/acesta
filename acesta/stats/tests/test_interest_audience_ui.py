from pathlib import Path
from types import SimpleNamespace
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_audience_iframe_loads_bootstrap_bundle_and_dynamic_tooltips():
    audience_module = (PROJECT_ROOT / "acesta/stats/dash/audience.py").read_text()
    tooltip_script = (
        PROJECT_ROOT / "acesta/static/js/dashboard.audience.tooltips.js"
    ).read_text()

    assert '"/static/js/bootstrap.bundle.min.js"' in audience_module
    assert '"/static/js/dashboard.audience.tooltips.js"' in audience_module
    assert "\"#audience [data-bs-toggle='tooltip']\"" in tooltip_script
    assert "bootstrap.Tooltip.getOrCreateInstance(trigger)" in tooltip_script
    assert "new MutationObserver" in tooltip_script
    assert "tooltip.dispose()" in tooltip_script
    assert "var initializationFrame = null" in tooltip_script


def test_audience_tourism_tooltip_uses_bootstrap_title_and_bottom_placement():
    audience_module = (PROJECT_ROOT / "acesta/stats/dash/audience.py").read_text()
    tooltip_script = (
        PROJECT_ROOT / "acesta/static/js/dashboard.audience.tooltips.js"
    ).read_text()

    assert '"tt": tourism_titles.get(rec.tourism_type)' in audience_module
    assert '"data-bs-title": group.tt' in tooltip_script
    assert '"data-bs-placement": "bottom"' in tooltip_script
    assert 'title=f"{dict(settings.TOURISM_TYPES_OUTSIDE)' not in audience_module


def test_splitter_hint_is_conditional_and_remembered_for_ninety_days():
    template = (PROJECT_ROOT / "acesta/templates/dashboard/interest.html").read_text()
    script = (PROJECT_ROOT / "acesta/static/js/dashboard.interest.js").read_text()
    styles = (PROJECT_ROOT / "acesta/static/css/dashboard.css").read_text()

    assert 'id="interest-splitter-hint"' in template
    assert 'frame.contentDocument.querySelector(".audience-group")' in script
    assert "interestSplitterHintCookieDays = 90" in script
    assert '"; path=/; SameSite=Lax"' in script
    assert "dismissInterestSplitterHint();" in script
    assert ".interest-splitter-hint.is-visible" in styles
    assert "@media (max-width:991.98px)" in styles


def test_audience_title_bar_is_fixed_on_both_axes():
    audience_module = (PROJECT_ROOT / "acesta/stats/dash/audience.py").read_text()
    styles = (PROJECT_ROOT / "acesta/static/css/dashboard.css").read_text()

    assert "text-nowrap position-fixed" not in audience_module
    assert 'className="audience-title-bar"' in audience_module
    assert 'return "bg-white d-block pt-3 pb-1"' not in audience_module
    assert "#audience-title-container::before" not in styles
    assert (
        "#audience-title-container{--audience-title-height:46px;"
        "position:sticky;z-index:100;top:0;left:0;width:100%;max-width:100%" in styles
    )
    assert (
        "height:var(--audience-title-height);padding-top:4px;background:#fff" in styles
    )
    assert "#audience-title-container{position:relative;z-index:auto}" in styles
    assert ".audience-title-bar{position:fixed;z-index:100;top:4px" in styles
    assert ".audience-title-bar{display:flex;align-items:center" in styles
    assert "overflow:hidden;text-overflow:ellipsis" in styles
    assert "#audience-title-container{--audience-title-height:40px" in styles


def test_invalid_audience_object_returns_empty_state_instead_of_raising():
    from acesta.stats.dash import audience as audience_module

    with mock.patch.object(audience_module, "get_object_title", return_value=None):
        title, title_class, data = audience_module.update_audience(
            "999_museum_cities",
            user=SimpleNamespace(is_extended=True),
        )

    assert title == ""
    assert title_class == "d-none"
    assert "empty" in data


def test_settled_table_context_restores_audience_selection():
    from acesta.stats.dash.interest.interest import update_audience_key

    key = update_audience_key(
        {"row_id": "01", "row": 0},
        {
            "tourismType": "museum",
            "interesantArea": "cities",
            "sortBy": [{"column_id": "qty_display", "direction": "desc"}],
        },
        [{"code": "01"}],
    )

    assert key == "01_museum_cities"
