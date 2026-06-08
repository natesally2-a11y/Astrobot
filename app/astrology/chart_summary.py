"""Текстовое описание натальной карты для передачи в LLM и отображения."""
from __future__ import annotations

from app.astrology.calculations import Aspect, NatalChart
from app.astrology.constants import ZODIAC_SIGNS, sign_index


def chart_to_text(chart: NatalChart, name: str | None = None) -> str:
    """Компактное текстовое представление карты (для промпта/отладки)."""
    lines: list[str] = []
    if name:
        lines.append(f"Имя: {name}")

    if chart.ascendant is not None:
        lines.append(
            f"Асцендент: {ZODIAC_SIGNS[sign_index(chart.ascendant)]} "
            f"({chart.ascendant % 30:.1f}°)"
        )
    if chart.midheaven is not None:
        lines.append(
            f"MC (Середина неба): {ZODIAC_SIGNS[sign_index(chart.midheaven)]}"
        )

    lines.append("\nПланеты:")
    for p in chart.planets:
        retro = " (R)" if p.retrograde else ""
        house = f", дом {p.house}" if p.house else ""
        lines.append(f"  {p.symbol} {p.name}: {p.sign} {p.degree:.1f}°{retro}{house}")

    if chart.aspects:
        lines.append("\nОсновные аспекты:")
        for a in chart.aspects[:15]:
            lines.append(_aspect_line(chart, a))

    if not chart.has_time:
        lines.append(
            "\nПримечание: точное время рождения неизвестно — дома и Асцендент "
            "не рассчитаны, позиции Луны и быстрых точек приблизительны."
        )
    return "\n".join(lines)


def _aspect_line(chart: NatalChart, a: Aspect) -> str:
    p1 = chart.planet(a.body1)
    p2 = chart.planet(a.body2)
    n1 = p1.name if p1 else a.body1
    n2 = p2.name if p2 else a.body2
    return f"  {n1} {a.symbol} {n2} ({a.name}, орб {a.orb}°)"


def transits_to_text(transits: list[Aspect]) -> str:
    if not transits:
        return "Существенных транзитных аспектов сейчас нет."
    lines = ["Текущие транзиты:"]
    for a in transits[:12]:
        lines.append(f"  {a.body1} {a.symbol} {a.body2} ({a.name}, орб {a.orb}°)")
    return "\n".join(lines)
