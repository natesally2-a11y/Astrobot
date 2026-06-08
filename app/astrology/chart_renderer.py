"""Генерация круговой натальной карты в формате SVG."""
from __future__ import annotations

import math

from app.astrology.calculations import NatalChart
from app.astrology.constants import ZODIAC_SYMBOLS

# Цвета аспектов
ASPECT_COLORS = {
    "Соединение": "#f1c40f",
    "Оппозиция": "#e74c3c",
    "Тригон": "#2ecc71",
    "Квадрат": "#e67e22",
    "Секстиль": "#3498db",
}

ELEMENT_COLORS = ["#e74c3c", "#27ae60", "#f1c40f", "#3498db"]  # огонь, земля, воздух, вода


def _polar(cx: float, cy: float, radius: float, angle_deg: float) -> tuple[float, float]:
    """Перевод астрологической долготы в координаты.

    0° Овна слева (запад), движение против часовой стрелки — классическая
    ориентация натальной карты.
    """
    rad = math.radians(angle_deg)
    x = cx - radius * math.cos(rad)
    y = cy - radius * math.sin(rad)
    return x, y


def render_chart_svg(chart: NatalChart, size: int = 600) -> str:
    cx = cy = size / 2
    r_outer = size * 0.46
    r_zodiac_inner = size * 0.39
    r_planet = size * 0.31
    r_aspect = size * 0.27

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'width="{size}" height="{size}" font-family="Arial, sans-serif">'
    )
    parts.append(f'<rect width="{size}" height="{size}" fill="#0b1026"/>')

    # Внешний круг
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r_outer}" fill="none" '
        f'stroke="#3b4267" stroke-width="2"/>'
    )
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r_zodiac_inner}" fill="none" '
        f'stroke="#3b4267" stroke-width="1"/>'
    )

    # 12 секторов знаков
    for i in range(12):
        start_angle = i * 30
        x1, y1 = _polar(cx, cy, r_zodiac_inner, start_angle)
        x2, y2 = _polar(cx, cy, r_outer, start_angle)
        parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#3b4267" stroke-width="1"/>'
        )
        # Символ знака в середине сектора
        mid = start_angle + 15
        sx, sy = _polar(cx, cy, (r_zodiac_inner + r_outer) / 2, mid)
        color = ELEMENT_COLORS[i % 4]
        parts.append(
            f'<text x="{sx:.1f}" y="{sy:.1f}" fill="{color}" font-size="{size*0.04:.0f}" '
            f'text-anchor="middle" dominant-baseline="central">{ZODIAC_SYMBOLS[i]}</text>'
        )

    # Дома (если рассчитаны)
    if chart.houses:
        for cusp in chart.houses:
            hx1, hy1 = _polar(cx, cy, 0, cusp)
            hx2, hy2 = _polar(cx, cy, r_zodiac_inner, cusp)
            parts.append(
                f'<line x1="{cx}" y1="{cy}" x2="{hx2:.1f}" y2="{hy2:.1f}" '
                f'stroke="#2a2f4a" stroke-width="0.7"/>'
            )

    # Асцендент / MC
    if chart.ascendant is not None:
        ax, ay = _polar(cx, cy, r_outer, chart.ascendant)
        parts.append(
            f'<text x="{ax:.1f}" y="{ay:.1f}" fill="#ffffff" font-size="{size*0.025:.0f}" '
            f'text-anchor="middle">ASC</text>'
        )

    # Аспекты (линии в центре)
    for a in chart.aspects:
        p1 = chart.planet(a.body1)
        p2 = chart.planet(a.body2)
        if not p1 or not p2:
            continue
        x1, y1 = _polar(cx, cy, r_aspect, p1.longitude)
        x2, y2 = _polar(cx, cy, r_aspect, p2.longitude)
        color = ASPECT_COLORS.get(a.name, "#888")
        parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="1" opacity="0.6"/>'
        )

    # Планеты
    for p in chart.planets:
        px, py = _polar(cx, cy, r_planet, p.longitude)
        parts.append(
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{size*0.022:.1f}" '
            f'fill="#161c3a" stroke="#5b6aa0" stroke-width="1"/>'
        )
        retro = "ᴿ" if p.retrograde else ""
        parts.append(
            f'<text x="{px:.1f}" y="{py:.1f}" fill="#ffd97a" font-size="{size*0.03:.0f}" '
            f'text-anchor="middle" dominant-baseline="central">{p.symbol}{retro}</text>'
        )

    # Центр
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r_aspect}" fill="none" '
        f'stroke="#2a2f4a" stroke-width="1"/>'
    )
    parts.append("</svg>")
    return "".join(parts)
