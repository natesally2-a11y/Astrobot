"""
SVG natal chart renderer.
Generates a beautiful dark-themed astrological chart.
"""
from __future__ import annotations

import math
import io
from typing import Optional
from app.astrology.calculations import NatalChart, ZODIAC_SYMBOLS, PLANET_SYMBOLS

SIZE = 600
CENTER = SIZE // 2
OUTER_RADIUS = 260
ZODIAC_RING_WIDTH = 35
PLANET_RING_RADIUS = 195
HOUSE_RADIUS = 170
INNER_RADIUS = 70

SIGN_COLORS = [
    "#FF6B6B", "#FF8E53", "#FFC93C", "#A8E063",
    "#56CCF2", "#6FCF97", "#F2994A", "#BB6BD9",
    "#2D9CDB", "#56CCF2", "#9B51E0", "#6FCF97",
]

ASPECT_COLORS = {
    "Соединение": "#FFD700",
    "Оппозиция": "#FF4444",
    "Тригон": "#44FF88",
    "Квадрат": "#FF6644",
    "Секстиль": "#4488FF",
    "Полусекстиль": "#AAAAAA",
    "Квинконс": "#AA44FF",
}


def _polar_to_xy(angle_deg: float, radius: float, cx: float = CENTER, cy: float = CENTER) -> tuple[float, float]:
    """Convert astrological angle (0=Aries at right, going counterclockwise) to SVG xy."""
    rad = math.radians(180 - angle_deg)
    x = cx + radius * math.cos(rad)
    y = cy + radius * math.sin(rad)
    return x, y


def render_natal_chart_svg(chart: NatalChart, title: str = "Натальная карта") -> str:
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" width="{SIZE}" height="{SIZE}">',
        '<defs>',
        '  <radialGradient id="bgGrad" cx="50%" cy="50%" r="50%">',
        '    <stop offset="0%" style="stop-color:#1a1a3e;stop-opacity:1" />',
        '    <stop offset="100%" style="stop-color:#0d0d1f;stop-opacity:1" />',
        '  </radialGradient>',
        '  <filter id="glow">',
        '    <feGaussianBlur stdDeviation="2" result="coloredBlur"/>',
        '    <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>',
        '  </filter>',
        '</defs>',
        f'<rect width="{SIZE}" height="{SIZE}" fill="url(#bgGrad)"/>',
    ]

    lines.extend(_draw_stars())
    lines.extend(_draw_zodiac_ring())
    lines.extend(_draw_circles())
    lines.extend(_draw_house_lines(chart))
    lines.extend(_draw_aspect_lines(chart))
    lines.extend(_draw_planets(chart))
    lines.extend(_draw_title(title, chart))

    lines.append('</svg>')
    return "\n".join(lines)


def _draw_stars() -> list[str]:
    import random
    rng = random.Random(42)
    lines = []
    for _ in range(80):
        x = rng.uniform(10, SIZE - 10)
        y = rng.uniform(10, SIZE - 10)
        r = rng.uniform(0.5, 1.5)
        opacity = rng.uniform(0.3, 0.9)
        lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="white" opacity="{opacity:.1f}"/>')
    return lines


def _draw_circles() -> list[str]:
    lines = []
    for r, color, width in [
        (OUTER_RADIUS, "#4a4a7a", "1.5"),
        (OUTER_RADIUS - ZODIAC_RING_WIDTH, "#3a3a6a", "1"),
        (HOUSE_RADIUS, "#2a2a5a", "0.8"),
        (INNER_RADIUS, "#3a3a6a", "1"),
    ]:
        lines.append(
            f'<circle cx="{CENTER}" cy="{CENTER}" r="{r}" '
            f'fill="none" stroke="{color}" stroke-width="{width}"/>'
        )
    return lines


def _draw_zodiac_ring() -> list[str]:
    lines = []
    zodiac_radius = OUTER_RADIUS - ZODIAC_RING_WIDTH / 2

    for i in range(12):
        start_angle = i * 30
        end_angle = (i + 1) * 30
        color = SIGN_COLORS[i]

        x1, y1 = _polar_to_xy(start_angle, OUTER_RADIUS - ZODIAC_RING_WIDTH)
        x2, y2 = _polar_to_xy(start_angle, OUTER_RADIUS)
        lines.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#4a4a7a" stroke-width="1.5"/>'
        )

        mid_angle = start_angle + 15
        tx, ty = _polar_to_xy(mid_angle, zodiac_radius)
        symbol = ZODIAC_SYMBOLS[i]
        lines.append(
            f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" dominant-baseline="central" '
            f'font-size="16" fill="{color}" filter="url(#glow)">{symbol}</text>'
        )

    return lines


def _draw_house_lines(chart: NatalChart) -> list[str]:
    lines = []
    if not chart.houses:
        for i in range(12):
            angle = i * 30 + chart.ascendant
            x1, y1 = _polar_to_xy(angle, INNER_RADIUS)
            x2, y2 = _polar_to_xy(angle, OUTER_RADIUS - ZODIAC_RING_WIDTH)
            opacity = "0.8" if i % 3 == 0 else "0.4"
            lines.append(
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="#5a5a9a" stroke-width="0.8" stroke-dasharray="3,3" opacity="{opacity}"/>'
            )
        return lines

    for i, cusp in enumerate(chart.houses[:12]):
        x1, y1 = _polar_to_xy(cusp, INNER_RADIUS)
        x2, y2 = _polar_to_xy(cusp, OUTER_RADIUS - ZODIAC_RING_WIDTH)
        is_angle = i in (0, 3, 6, 9)
        color = "#8888cc" if is_angle else "#5a5a9a"
        width = "1.5" if is_angle else "0.8"
        dash = "" if is_angle else 'stroke-dasharray="3,3"'
        lines.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="{width}" {dash}/>'
        )

        nx, ny = _polar_to_xy(cusp + 15, HOUSE_RADIUS + 5)
        lines.append(
            f'<text x="{nx:.1f}" y="{ny:.1f}" text-anchor="middle" dominant-baseline="central" '
            f'font-size="10" fill="#7777aa" opacity="0.7">{i + 1}</text>'
        )

    return lines


def _draw_aspect_lines(chart: NatalChart) -> list[str]:
    lines = []
    shown = set()
    for aspect in chart.aspects:
        key = (aspect.planet1, aspect.planet2)
        if key in shown:
            continue
        shown.add(key)

        p1 = chart.planets.get(aspect.planet1)
        p2 = chart.planets.get(aspect.planet2)
        if not p1 or not p2:
            continue

        x1, y1 = _polar_to_xy(p1.longitude, INNER_RADIUS - 10)
        x2, y2 = _polar_to_xy(p2.longitude, INNER_RADIUS - 10)
        color = ASPECT_COLORS.get(aspect.aspect_name, "#888888")
        opacity = max(0.2, 0.7 - aspect.orb * 0.05)
        lines.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="0.8" opacity="{opacity:.2f}"/>'
        )

    return lines


def _draw_planets(chart: NatalChart) -> list[str]:
    lines = []
    planet_order = ["Sun", "Moon", "Mercury", "Venus", "Mars",
                    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Ascendant"]

    placed: list[float] = []

    for name in planet_order:
        planet = chart.planets.get(name)
        if not planet:
            continue

        lon = planet.longitude
        adjusted_lon = _avoid_overlap(lon, placed)
        placed.append(adjusted_lon)

        px, py = _polar_to_xy(adjusted_lon, PLANET_RING_RADIUS)
        symbol = PLANET_SYMBOLS.get(name, "●")
        color = "#FFD700" if name in ("Sun", "Ascendant") else "#C0C0C0"
        if name == "Moon":
            color = "#E8E8FF"
        if planet.retrograde:
            color = "#FF8888"

        lines.append(
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="14" '
            f'fill="#1a1a3e" stroke="{color}" stroke-width="1.5" opacity="0.9"/>'
        )
        lines.append(
            f'<text x="{px:.1f}" y="{py:.1f}" text-anchor="middle" dominant-baseline="central" '
            f'font-size="12" fill="{color}" filter="url(#glow)">{symbol}</text>'
        )

        if planet.retrograde:
            rx, ry = px + 9, py - 9
            lines.append(
                f'<text x="{rx:.1f}" y="{ry:.1f}" font-size="7" fill="#FF8888">℞</text>'
            )

        tick_x1, tick_y1 = _polar_to_xy(lon, OUTER_RADIUS - ZODIAC_RING_WIDTH - 2)
        tick_x2, tick_y2 = _polar_to_xy(lon, OUTER_RADIUS - ZODIAC_RING_WIDTH - 8)
        lines.append(
            f'<line x1="{tick_x1:.1f}" y1="{tick_y1:.1f}" x2="{tick_x2:.1f}" y2="{tick_y2:.1f}" '
            f'stroke="{color}" stroke-width="1.5"/>'
        )

    return lines


def _avoid_overlap(lon: float, placed: list[float], min_gap: float = 15.0) -> float:
    adjusted = lon
    for p in placed:
        diff = abs(adjusted - p) % 360
        if diff > 180:
            diff = 360 - diff
        if diff < min_gap:
            adjusted = (adjusted + min_gap) % 360
    return adjusted


def _draw_title(title: str, chart: NatalChart) -> list[str]:
    lines = [
        f'<text x="{CENTER}" y="30" text-anchor="middle" font-size="14" '
        f'fill="#9999cc" font-family="serif">✦ {title} ✦</text>',
    ]

    sun_sign = chart.get_sun_sign() if chart.planets else ""
    if sun_sign:
        asc = chart.get_ascendant_sign()
        moon = chart.get_moon_sign()
        info = f"☉ {sun_sign}"
        if moon and moon != "Неизвестно":
            info += f"  ☽ {moon}"
        if asc and asc != "Неизвестно":
            info += f"  ↑ {asc}"
        lines.append(
            f'<text x="{CENTER}" y="{SIZE - 15}" text-anchor="middle" font-size="11" '
            f'fill="#7777aa">{info}</text>'
        )

    return lines
