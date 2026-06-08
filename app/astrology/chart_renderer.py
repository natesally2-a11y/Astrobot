"""SVG natal chart renderer (no external drawing dependencies)."""
from __future__ import annotations

import math
from typing import List

from app.astrology.calculations import NatalChart
from app.astrology.constants import (
    ASPECT_COLORS,
    ELEMENT_COLORS,
    PLANET_GLYPHS,
    SIGN_GLYPHS,
    SIGNS,
)


def _polar(cx: float, cy: float, radius: float, longitude: float) -> tuple[float, float]:
    """Map an ecliptic longitude to an (x, y) point on the wheel.

    0° Aries sits at the 9 o'clock position; longitude increases counter-clockwise.
    """
    theta = math.radians(180.0 - longitude)
    x = cx + radius * math.cos(theta)
    y = cy - radius * math.sin(theta)
    return x, y


def render_natal_chart_svg(chart: NatalChart, size: int = 600) -> str:
    cx = cy = size / 2
    r_outer = size * 0.46
    r_zodiac_inner = size * 0.38
    r_planets = size * 0.30
    r_aspect = size * 0.27

    parts: List[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'width="{size}" height="{size}" font-family="Georgia, serif">'
    )
    # Background.
    parts.append(
        f'<defs><radialGradient id="bg" cx="50%" cy="50%" r="60%">'
        f'<stop offset="0%" stop-color="#1b1140"/>'
        f'<stop offset="100%" stop-color="#070514"/></radialGradient></defs>'
    )
    parts.append(f'<rect width="{size}" height="{size}" fill="url(#bg)"/>')

    # Outer / inner rings.
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r_outer}" fill="none" stroke="#b8a6ff" stroke-width="2"/>'
    )
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r_zodiac_inner}" fill="none" stroke="#6d5bbf" stroke-width="1"/>'
    )
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r_aspect}" fill="none" stroke="#3a2f66" stroke-width="1"/>'
    )

    # Zodiac sectors (12 x 30°).
    for i, sign in enumerate(SIGNS):
        start_lon = i * 30
        # Sector divider line.
        x1, y1 = _polar(cx, cy, r_zodiac_inner, start_lon)
        x2, y2 = _polar(cx, cy, r_outer, start_lon)
        parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#6d5bbf" stroke-width="0.8"/>'
        )
        # Sign glyph in the middle of the sector.
        mid_lon = start_lon + 15
        gx, gy = _polar(cx, cy, (r_outer + r_zodiac_inner) / 2, mid_lon)
        color = ELEMENT_COLORS.get(sign[3], "#d9b54a")
        parts.append(
            f'<text x="{gx:.1f}" y="{gy + 7:.1f}" font-size="{size * 0.045:.0f}" '
            f'fill="{color}" text-anchor="middle">{SIGN_GLYPHS[i]}</text>'
        )

    # House cusps + Ascendant / MC markers.
    if chart.has_houses and chart.houses:
        for cusp in chart.houses:
            x1, y1 = _polar(cx, cy, 0, cusp)
            x2, y2 = _polar(cx, cy, r_aspect, cusp)
            parts.append(
                f'<line x1="{cx}" y1="{cy}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="#2a2350" stroke-width="0.6"/>'
            )
        if chart.ascendant is not None:
            ax, ay = _polar(cx, cy, r_outer + 4, chart.ascendant)
            parts.append(
                f'<text x="{ax:.1f}" y="{ay:.1f}" font-size="14" fill="#ffd86b" '
                f'text-anchor="middle">ASC</text>'
            )
        if chart.midheaven is not None:
            mx, my = _polar(cx, cy, r_outer + 4, chart.midheaven)
            parts.append(
                f'<text x="{mx:.1f}" y="{my:.1f}" font-size="14" fill="#ffd86b" '
                f'text-anchor="middle">MC</text>'
            )

    # Aspect lines (drawn first so glyphs sit on top).
    pos_by_key = {p.key: p for p in chart.planets}
    for asp in chart.aspects:
        p1 = pos_by_key.get(asp.body1)
        p2 = pos_by_key.get(asp.body2)
        if not p1 or not p2:
            continue
        x1, y1 = _polar(cx, cy, r_aspect, p1.longitude)
        x2, y2 = _polar(cx, cy, r_aspect, p2.longitude)
        color = ASPECT_COLORS.get(asp.key, "#888")
        parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="1" opacity="0.55"/>'
        )

    # Planet glyphs.
    for p in chart.planets:
        px, py = _polar(cx, cy, r_planets, p.longitude)
        # Tick from ring to planet.
        tx, ty = _polar(cx, cy, r_zodiac_inner, p.longitude)
        parts.append(
            f'<line x1="{tx:.1f}" y1="{ty:.1f}" x2="{px:.1f}" y2="{py:.1f}" '
            f'stroke="#5a4f8a" stroke-width="0.6"/>'
        )
        glyph = PLANET_GLYPHS.get(p.key, "?")
        retro = "↺" if p.retrograde else ""
        parts.append(
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="12" fill="#0d0a24" '
            f'stroke="#b8a6ff" stroke-width="0.8"/>'
        )
        parts.append(
            f'<text x="{px:.1f}" y="{py + 5:.1f}" font-size="16" fill="#ffffff" '
            f'text-anchor="middle">{glyph}</text>'
        )
        if retro:
            parts.append(
                f'<text x="{px + 11:.1f}" y="{py - 8:.1f}" font-size="9" '
                f'fill="#ff8080" text-anchor="middle">{retro}</text>'
            )

    # Center label.
    parts.append(
        f'<text x="{cx}" y="{cy + 5:.1f}" font-size="13" fill="#8a7fc0" '
        f'text-anchor="middle">Stellarium AI</text>'
    )

    parts.append("</svg>")
    return "".join(parts)


def svg_to_png_bytes(svg: str) -> bytes | None:
    """Best-effort SVG -> PNG conversion if a rasteriser is available.

    Returns None when no rasteriser is installed; callers should then fall back
    to sending the SVG document directly (Telegram can display it as a document).
    """
    try:
        import cairosvg  # type: ignore

        return cairosvg.svg2png(bytestring=svg.encode("utf-8"))
    except Exception:
        return None
