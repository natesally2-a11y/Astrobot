"""Tests for the astrology calculation engine."""
import datetime as dt

from app.astrology.calculations import calculate_natal_chart, calculate_transits
from app.astrology.constants import SIGN_NAMES_RU, degree_to_sign
from app.astrology.service import build_chart


def test_degree_to_sign():
    assert degree_to_sign(0)[0] == 0          # 0° Aries
    assert degree_to_sign(35)[0] == 1         # 5° Taurus
    assert round(degree_to_sign(35)[1], 2) == 5.0
    assert degree_to_sign(359.9)[0] == 11     # Pisces


def test_sun_sign_known_date():
    # 15 July 1990, 14:30 Moscow -> Sun in Cancer.
    chart = build_chart(dt.date(1990, 7, 15), dt.time(14, 30), 55.7558, 37.6173, "Europe/Moscow")
    sun = chart.planet("sun")
    assert sun is not None
    assert SIGN_NAMES_RU[sun.sign_index] == "Рак"


def test_houses_present_when_time_known():
    chart = build_chart(dt.date(1990, 7, 15), dt.time(14, 30), 55.7558, 37.6173, "Europe/Moscow")
    assert chart.has_houses
    assert chart.ascendant is not None
    assert len(chart.houses) == 12


def test_no_houses_when_time_unknown():
    chart = build_chart(dt.date(1990, 7, 15), None, 55.7558, 37.6173, "Europe/Moscow")
    assert not chart.has_houses
    assert chart.ascendant is None


def test_aspects_are_sorted_by_orb():
    chart = build_chart(dt.date(1990, 7, 15), dt.time(14, 30), 55.7558, 37.6173, "Europe/Moscow")
    orbs = [a.orb for a in chart.aspects]
    assert orbs == sorted(orbs)


def test_transits_return_aspects():
    chart = build_chart(dt.date(1990, 7, 15), dt.time(14, 30), 55.7558, 37.6173, "Europe/Moscow")
    transits = calculate_transits(chart, dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc))
    assert isinstance(transits, list)
    assert all(a.orb >= 0 for a in transits)
