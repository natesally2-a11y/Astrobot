"""Tests for SVG rendering and AI interpreter mock."""
import asyncio
import datetime as dt

from app.astrology.ai_interpreter import chart_summary, interpret_natal
from app.astrology.chart_renderer import render_natal_chart_svg
from app.astrology.service import build_chart


def _chart():
    return build_chart(dt.date(1990, 7, 15), dt.time(14, 30), 55.7558, 37.6173, "Europe/Moscow")


def test_svg_render_basic():
    svg = render_natal_chart_svg(_chart())
    assert svg.startswith("<svg")
    assert svg.rstrip().endswith("</svg>")
    assert "Stellarium AI" in svg


def test_chart_summary_contains_planets():
    summary = chart_summary(_chart(), name="Тест")
    assert "Солнце" in summary
    assert "Асцендент" in summary


def test_interpret_natal_mock(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "openai_mock", True)
    result = asyncio.run(interpret_natal(_chart(), name="Тест"))
    assert isinstance(result, str)
    assert len(result) > 20
