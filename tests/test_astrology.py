from datetime import date, time

from app.astrology.calculations import calculate_natal_chart, compatibility_score


def test_calculate_natal_chart_returns_planets_and_aspects():
    chart = calculate_natal_chart(
        birth_date=date(1994, 11, 17),
        birth_time=time(9, 30),
        birth_place="Moscow, Russia",
        latitude=55.7558,
        longitude=37.6176,
        timezone_name="Europe/Moscow",
    )

    assert len(chart.planets) == 10
    assert chart.summary
    assert all(1 <= planet.house <= 12 for planet in chart.planets)


def test_compatibility_score_is_bounded():
    first_chart = calculate_natal_chart(
        birth_date=date(1994, 11, 17),
        birth_time=time(9, 30),
        birth_place="Moscow, Russia",
        latitude=55.7558,
        longitude=37.6176,
        timezone_name="Europe/Moscow",
    )
    second_chart = calculate_natal_chart(
        birth_date=date(1993, 8, 14),
        birth_time=time(18, 20),
        birth_place="Saint Petersburg, Russia",
        latitude=59.9343,
        longitude=30.3351,
        timezone_name="Europe/Moscow",
    )

    result = compatibility_score(first_chart, second_chart)
    assert 0 <= result["score"] <= 100
    assert "summary" in result
