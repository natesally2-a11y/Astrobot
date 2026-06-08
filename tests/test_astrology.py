from datetime import date, time

from app.astrology.calculations import calculate_natal_chart, important_transits
from app.astrology.chart_renderer import render_chart_svg


def test_calculate_natal_chart_contains_core_planets() -> None:
    chart = calculate_natal_chart(date(1992, 3, 24), time(8, 45), "Moscow", 55.7558, 37.6173)

    assert len(chart.planets) == 7
    assert {planet.key for planet in chart.planets} >= {"Sun", "Moon", "Mercury"}
    assert all(1 <= planet.house <= 12 for planet in chart.planets if planet.house is not None)


def test_render_chart_svg() -> None:
    chart = calculate_natal_chart(date(1992, 3, 24), None, "Moscow", None, None)
    svg = render_chart_svg(chart)

    assert svg.startswith("<svg")
    assert "Moscow" in svg


def test_important_transits_returns_list() -> None:
    chart = calculate_natal_chart(date(1992, 3, 24), None, "Moscow", None, None)

    assert isinstance(important_transits(chart), list)
