"""Render a NatalChart into an SVG string.

The renderer is intentionally dependency-free (no matplotlib/cairo): it builds
the SVG markup directly so that the Mini App can serve it as a static page or
inline ``<svg>`` element.
"""
from __future__ import annotations

import math
from typing import List

from app.astrology.calculations import NatalChart, PLANETS, ZODIAC_SIGNS

# Visual constants
SVG_SIZE = 600
CENTER = SVG_SIZE / 2
OUTER_RADIUS = CENTER - 20
INNER_RADIUS = OUTER_RADIUS - 50          # zodiac ring inner edge
HOUSE_RADIUS = INNER_RADIUS - 30          # planet placement radius
HOUSE_INNER = HOUSE_RADIUS - 60

# Zodiac slice colours — alternating for legibility.
SIGN_COLORS = [
    "#F4D35E", "#EE964B", "#F95738", "#9A031E",
    "#5F0F40", "#3A0CA3", "#3F37C9", "#4361EE",
    "#4CC9F0", "#80FFDB", "#56AB91", "#A7C957",
]

PLANET_COLORS = {
    "Sun":     "#FFB703",
    "Moon":    "#E0E1DD",
    "Mercury": "#9D4EDD",
    "Venus":   "#FF99C8",
    "Mars":    "#E63946",
    "Jupiter": "#F77F00",
    "Saturn":  "#6A4C93",
    "Uranus":  "#118AB2",
    "Neptune": "#073B4C",
    "Pluto":   "#8D99AE",
}

ASPECT_COLORS = {
    "conjunction": "#ffffff",
    "opposition":  "#e63946",
    "square":      "#f48c06",
    "trine":       "#90be6d",
    "sextile":     "#48cae4",
}


def _polar(angle_deg: float, radius: float) -> tuple[float, float]:
    """Convert an ecliptic angle (0° = Aries, CCW) to SVG coordinates.

    SVG y grows downward; we put 0° Aries on the *left* (9 o'clock) and run
    counter-clockwise, matching classical natal-chart orientation.
    """
    a = math.radians(180 - angle_deg)
    x = CENTER + radius * math.cos(a)
    y = CENTER - radius * math.sin(a)
    return x, y


def _arc_path(start_angle: float, end_angle: float, radius: float) -> str:
    x1, y1 = _polar(start_angle, radius)
    x2, y2 = _polar(end_angle, radius)
    sweep = 0  # counter-clockwise
    large_arc = 1 if (end_angle - start_angle) % 360 > 180 else 0
    return f"M {x1:.2f} {y1:.2f} A {radius} {radius} 0 {large_arc} {sweep} {x2:.2f} {y2:.2f}"


def _sign_sector(idx: int) -> str:
    start = idx * 30
    end = start + 30
    x1, y1 = _polar(start, OUTER_RADIUS)
    x2, y2 = _polar(end, OUTER_RADIUS)
    x3, y3 = _polar(end, INNER_RADIUS)
    x4, y4 = _polar(start, INNER_RADIUS)
    color = SIGN_COLORS[idx % 12]
    return (
        f'<path d="M {x1:.2f} {y1:.2f} '
        f'A {OUTER_RADIUS} {OUTER_RADIUS} 0 0 0 {x2:.2f} {y2:.2f} '
        f"L {x3:.2f} {y3:.2f} "
        f'A {INNER_RADIUS} {INNER_RADIUS} 0 0 1 {x4:.2f} {y4:.2f} Z" '
        f'fill="{color}" fill-opacity="0.35" stroke="#1b1b3a" stroke-width="1"/>'
    )


def _sign_glyphs() -> List[str]:
    out = []
    for idx, (_en, _ru, glyph) in enumerate(ZODIAC_SIGNS):
        x, y = _polar(idx * 30 + 15, (OUTER_RADIUS + INNER_RADIUS) / 2)
        out.append(
            f'<text x="{x:.2f}" y="{y + 6:.2f}" text-anchor="middle" '
            f'font-size="22" fill="#fff">{glyph}</text>'
        )
    return out


def _house_lines(chart: NatalChart) -> List[str]:
    if not chart.houses:
        return []
    out = []
    for i, cusp in enumerate(chart.houses):
        x1, y1 = _polar(cusp, INNER_RADIUS)
        x2, y2 = _polar(cusp, 0)  # to center
        stroke = "#ffffff" if i in (0, 3, 6, 9) else "rgba(255,255,255,0.35)"
        width = 2 if i in (0, 3, 6, 9) else 1
        out.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{stroke}" stroke-width="{width}"/>'
        )
    return out


def _aspect_lines(chart: NatalChart) -> List[str]:
    out = []
    for asp in chart.aspects:
        a = chart.planets[asp.planet_a]
        b = chart.planets[asp.planet_b]
        x1, y1 = _polar(a.longitude, HOUSE_INNER)
        x2, y2 = _polar(b.longitude, HOUSE_INNER)
        color = ASPECT_COLORS.get(asp.name, "#ffffff")
        out.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{color}" stroke-width="1.2" stroke-opacity="0.7"/>'
        )
    return out


def _planet_markers(chart: NatalChart) -> List[str]:
    out = []
    # De-clutter glyphs by nudging overlapping planets.
    placed: list[float] = []
    for name, p in chart.planets.items():
        angle = p.longitude
        for prev in placed:
            if abs(angle - prev) < 6:
                angle += 6
        placed.append(angle)
        x, y = _polar(angle, HOUSE_RADIUS)
        color = PLANET_COLORS.get(name, "#ffffff")
        out.append(
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="11" fill="#0d1b2a" '
            f'stroke="{color}" stroke-width="2"/>'
        )
        out.append(
            f'<text x="{x:.2f}" y="{y + 5:.2f}" text-anchor="middle" '
            f'font-size="14" fill="{color}">{p.glyph}</text>'
        )
    return out


def _angles_markers(chart: NatalChart) -> List[str]:
    out = []
    if chart.ascendant is not None:
        x, y = _polar(chart.ascendant, OUTER_RADIUS + 12)
        out.append(
            f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="middle" '
            f'font-size="14" fill="#ffd166">ASC</text>'
        )
    if chart.midheaven is not None:
        x, y = _polar(chart.midheaven, OUTER_RADIUS + 12)
        out.append(
            f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="middle" '
            f'font-size="14" fill="#06d6a0">MC</text>'
        )
    return out


def render_svg(chart: NatalChart) -> str:
    """Render a NatalChart into a self-contained SVG string."""
    parts: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {SVG_SIZE} {SVG_SIZE}" width="100%" height="100%">',
        # Background gradient
        '<defs>'
        '<radialGradient id="bg" cx="50%" cy="50%" r="50%">'
        '<stop offset="0%" stop-color="#1b1b3a"/>'
        '<stop offset="100%" stop-color="#06061a"/>'
        '</radialGradient>'
        '</defs>',
        f'<rect width="{SVG_SIZE}" height="{SVG_SIZE}" fill="url(#bg)"/>',
        f'<circle cx="{CENTER}" cy="{CENTER}" r="{OUTER_RADIUS}" fill="none" '
        f'stroke="#ffffff" stroke-width="2"/>',
        f'<circle cx="{CENTER}" cy="{CENTER}" r="{INNER_RADIUS}" fill="none" '
        f'stroke="#ffffff" stroke-width="1"/>',
        f'<circle cx="{CENTER}" cy="{CENTER}" r="{HOUSE_INNER}" fill="none" '
        f'stroke="#ffffff" stroke-width="1" stroke-opacity="0.5"/>',
    ]
    parts += [_sign_sector(i) for i in range(12)]
    parts += _sign_glyphs()
    parts += _house_lines(chart)
    parts += _aspect_lines(chart)
    parts += _planet_markers(chart)
    parts += _angles_markers(chart)
    parts.append("</svg>")
    return "\n".join(parts)
