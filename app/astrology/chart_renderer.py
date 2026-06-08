from __future__ import annotations

import html
import math

from app.astrology.calculations import ASPECTS, SIGNS
from app.astrology.schemas import NatalChart

PLANET_GLYPHS = {
    "sun": "☉",
    "moon": "☽",
    "mercury": "☿",
    "venus": "♀",
    "mars": "♂",
    "jupiter": "♃",
    "saturn": "♄",
    "uranus": "♅",
    "neptune": "♆",
    "pluto": "♇",
}

ASPECT_COLORS = {
    "соединение": "#f59e0b",
    "секстиль": "#22c55e",
    "квадрат": "#ef4444",
    "тригон": "#38bdf8",
    "оппозиция": "#a855f7",
}


def _point(center: float, radius: float, longitude: float) -> tuple[float, float]:
    angle = math.radians(longitude - 90)
    return center + math.cos(angle) * radius, center + math.sin(angle) * radius


def render_chart_svg(chart: NatalChart, size: int = 720) -> str:
    center = size / 2
    outer = size * 0.43
    inner = size * 0.29
    planet_radius = size * 0.36
    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}" role="img">',
        "<defs>",
        '<radialGradient id="bg" cx="50%" cy="50%" r="50%">',
        '<stop offset="0%" stop-color="#1e1b4b"/>',
        '<stop offset="100%" stop-color="#020617"/>',
        "</radialGradient>",
        "</defs>",
        f'<rect width="{size}" height="{size}" rx="28" fill="url(#bg)"/>',
        f'<circle cx="{center}" cy="{center}" r="{outer}" fill="none" stroke="#e0e7ff" stroke-width="2"/>',
        f'<circle cx="{center}" cy="{center}" r="{inner}" fill="none" stroke="#64748b" stroke-width="1"/>',
    ]

    for sign_index, sign in enumerate(SIGNS):
        start = sign_index * 30
        x1, y1 = _point(center, outer, start)
        x2, y2 = _point(center, inner, start)
        tx, ty = _point(center, outer - 24, start + 15)
        lines.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#475569"/>')
        lines.append(
            f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" dominant-baseline="middle" '
            f'fill="#c7d2fe" font-size="12">{html.escape(sign[:3])}</text>'
        )

    planet_points: dict[str, tuple[float, float]] = {}
    for planet in chart.planets:
        x, y = _point(center, planet_radius, planet.longitude)
        planet_points[planet.label] = (x, y)
        glyph = PLANET_GLYPHS.get(planet.planet, planet.label[:1])
        lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="15" fill="#111827" stroke="#f8fafc"/>')
        lines.append(
            f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" dominant-baseline="middle" '
            f'fill="#f8fafc" font-size="18">{html.escape(glyph)}</text>'
        )

    for aspect in chart.aspects[:24]:
        if aspect.planet_a not in planet_points or aspect.planet_b not in planet_points:
            continue
        x1, y1 = planet_points[aspect.planet_a]
        x2, y2 = planet_points[aspect.planet_b]
        color = ASPECT_COLORS.get(aspect.aspect, "#94a3b8")
        width = 1.8 if aspect.angle in (0, 180) else 1.2
        lines.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="{width}" opacity="0.62"/>'
        )

    title = f"Натальная карта: {chart.profile.birth_place}"
    lines.append(
        f'<text x="{center}" y="{size - 34}" text-anchor="middle" fill="#f8fafc" '
        f'font-size="18" font-family="Inter, Arial">{html.escape(title)}</text>'
    )
    lines.append("</svg>")
    return "\n".join(lines)
