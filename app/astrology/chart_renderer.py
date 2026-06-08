"""SVG renderer for natal charts.

Produces a clean, readable circular chart with planets, sign sectors and a
simple aspect grid.  Intentionally self-contained — no external SVG libs.
"""

from __future__ import annotations

import math

from app.astrology.calculations import (
    NatalChart,
    PLANET_GLYPHS,
    SIGN_GLYPH,
)

ASPECT_COLORS = {
    "Conjunction": "#f5d76e",
    "Opposition": "#e74c3c",
    "Trine": "#27ae60",
    "Square": "#c0392b",
    "Sextile": "#3498db",
}


def render_chart_svg(chart: NatalChart, size: int = 520) -> str:
    cx = cy = size / 2
    r_outer = size * 0.48
    r_signs = size * 0.42
    r_inner = size * 0.34
    r_planets = size * 0.30
    r_aspects = size * 0.26

    def pol(r: float, angle_deg: float) -> tuple[float, float]:
        a = math.radians(180 - angle_deg)
        return cx + r * math.cos(a), cy + r * math.sin(a)

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'width="{size}" height="{size}" font-family="serif">'
    )

    parts.append(
        f'<defs>'
        f'<radialGradient id="bg" cx="50%" cy="50%" r="50%">'
        f'<stop offset="0%" stop-color="#10141f"/>'
        f'<stop offset="100%" stop-color="#05060d"/>'
        f'</radialGradient>'
        f'</defs>'
    )
    parts.append(f'<rect width="{size}" height="{size}" fill="url(#bg)"/>')

    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r_outer}" '
        f'fill="none" stroke="#e6e6f0" stroke-width="1.5"/>'
    )
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r_inner}" '
        f'fill="none" stroke="#9ea3b8" stroke-width="1"/>'
    )
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r_aspects}" '
        f'fill="none" stroke="#4a4f6b" stroke-width="0.5"/>'
    )

    for i in range(12):
        ang = i * 30
        x1, y1 = pol(r_inner, ang)
        x2, y2 = pol(r_outer, ang)
        parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#9ea3b8" stroke-width="0.7"/>'
        )
        gx, gy = pol((r_outer + r_inner) / 2, ang + 15)
        parts.append(
            f'<text x="{gx:.1f}" y="{gy:.1f}" font-size="20" fill="#f5d76e" '
            f'text-anchor="middle" dominant-baseline="middle">{SIGN_GLYPH[i]}</text>'
        )

    if chart.houses:
        for cusp in chart.houses:
            x1, y1 = pol(r_aspects, cusp)
            x2, y2 = pol(r_inner, cusp)
            parts.append(
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="#5a6076" stroke-width="0.5" stroke-dasharray="3,3"/>'
            )

    if chart.ascendant is not None:
        ax, ay = pol(r_outer + 14, chart.ascendant)
        parts.append(
            f'<text x="{ax:.1f}" y="{ay:.1f}" font-size="13" fill="#ffffff" '
            f'text-anchor="middle">Asc</text>'
        )
    if chart.midheaven is not None:
        mx, my = pol(r_outer + 14, chart.midheaven)
        parts.append(
            f'<text x="{mx:.1f}" y="{my:.1f}" font-size="13" fill="#ffffff" '
            f'text-anchor="middle">MC</text>'
        )

    placed: list[float] = []
    for name, pos in chart.positions.items():
        angle = pos.longitude
        for existing in placed:
            if abs(((angle - existing + 180) % 360) - 180) < 6:
                angle += 6
        placed.append(angle)
        px, py = pol(r_planets, angle)
        parts.append(
            f'<text x="{px:.1f}" y="{py:.1f}" font-size="22" fill="#ffffff" '
            f'text-anchor="middle" dominant-baseline="middle">{PLANET_GLYPHS[name]}</text>'
        )
        lx, ly = pol(r_planets - 18, angle)
        parts.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="9" fill="#cdd3ea" '
            f'text-anchor="middle" dominant-baseline="middle">{int(pos.degree_in_sign)}°</text>'
        )

    for asp in chart.aspects:
        a_pos = chart.positions[asp.body_a]
        b_pos = chart.positions[asp.body_b]
        ax, ay = pol(r_aspects, a_pos.longitude)
        bx, by = pol(r_aspects, b_pos.longitude)
        color = ASPECT_COLORS.get(asp.aspect, "#888")
        parts.append(
            f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" '
            f'stroke="{color}" stroke-width="0.8" opacity="0.7"/>'
        )

    parts.append(
        f'<text x="{cx}" y="{size - 16}" font-size="11" fill="#9ea3b8" '
        f'text-anchor="middle">Stellarium AI · натальная карта</text>'
    )

    parts.append("</svg>")
    return "".join(parts)
