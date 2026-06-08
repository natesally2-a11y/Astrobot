"""SVG natal chart renderer."""

import math
from app.astrology.calculations import NatalChart, ZODIAC_SYMBOLS, PLANET_SYMBOLS, ZODIAC_SIGNS

SIGN_COLORS = [
    "#E74C3C", "#27AE60", "#F39C12", "#3498DB",
    "#E74C3C", "#27AE60", "#F39C12", "#3498DB",
    "#E74C3C", "#27AE60", "#F39C12", "#3498DB",
]

ELEMENT_COLORS = {
    "fire": "#E74C3C",
    "earth": "#27AE60",
    "air": "#F39C12",
    "water": "#3498DB",
}

ASPECT_COLORS = {
    "Соединение": "#9B59B6",
    "Секстиль": "#2ECC71",
    "Квадрат": "#E74C3C",
    "Тригон": "#3498DB",
    "Оппозиция": "#E67E22",
}


def _polar_to_cartesian(cx: float, cy: float, r: float, angle_deg: float) -> tuple[float, float]:
    angle_rad = math.radians(angle_deg)
    x = cx + r * math.cos(angle_rad)
    y = cy - r * math.sin(angle_rad)
    return x, y


def render_natal_chart_svg(chart: NatalChart, size: int = 600) -> str:
    """Render a natal chart as an SVG string."""
    cx, cy = size / 2, size / 2
    outer_r = size * 0.44
    zodiac_r = size * 0.38
    inner_r = size * 0.30
    planet_r = size * 0.24
    aspect_r = size * 0.18
    center_r = size * 0.05

    asc_offset = chart.ascendant

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'width="{size}" height="{size}" '
        f'style="background:#0D1117;border-radius:50%">'
    )

    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{outer_r}" fill="none" stroke="#30363D" stroke-width="2"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{zodiac_r}" fill="none" stroke="#30363D" stroke-width="1.5"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{inner_r}" fill="none" stroke="#30363D" stroke-width="1.5"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{center_r}" fill="#161B22" stroke="#30363D" stroke-width="1"/>')

    for i in range(12):
        angle = asc_offset - i * 30
        x1, y1 = _polar_to_cartesian(cx, cy, inner_r, angle)
        x2, y2 = _polar_to_cartesian(cx, cy, outer_r, angle)
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#30363D" stroke-width="1"/>')

    for i in range(12):
        mid_angle = asc_offset - i * 30 - 15
        sx, sy = _polar_to_cartesian(cx, cy, (zodiac_r + outer_r) / 2, mid_angle)
        color = SIGN_COLORS[i]
        symbol = ZODIAC_SYMBOLS[i]
        parts.append(
            f'<text x="{sx:.1f}" y="{sy:.1f}" fill="{color}" font-size="16" '
            f'text-anchor="middle" dominant-baseline="central" font-family="serif">{symbol}</text>'
        )

    if chart.houses:
        for i, house in enumerate(chart.houses):
            cusp_angle = asc_offset - (house.degree + ZODIAC_SIGNS.index(house.sign) * 30 - chart.ascendant)
            normalized = cusp_angle % 360

            x1, y1 = _polar_to_cartesian(cx, cy, center_r, normalized)
            x2, y2 = _polar_to_cartesian(cx, cy, inner_r, normalized)

            sw = "1.5" if house.number in (1, 4, 7, 10) else "0.5"
            col = "#58A6FF" if house.number in (1, 4, 7, 10) else "#30363D"
            parts.append(
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="{col}" stroke-width="{sw}" stroke-dasharray="4,2"/>'
            )

            label_angle = normalized - 15
            lx, ly = _polar_to_cartesian(cx, cy, inner_r * 0.85, label_angle)
            parts.append(
                f'<text x="{lx:.1f}" y="{ly:.1f}" fill="#484F58" font-size="10" '
                f'text-anchor="middle" dominant-baseline="central">{house.number}</text>'
            )

    used_angles: list[float] = []
    for p in chart.planets:
        raw_angle = asc_offset - (p.longitude - chart.ascendant)
        angle = raw_angle % 360

        for ua in used_angles:
            if abs(angle - ua) < 8:
                angle += 9
                break
        used_angles.append(angle)

        px, py = _polar_to_cartesian(cx, cy, planet_r, angle)
        tick_x, tick_y = _polar_to_cartesian(cx, cy, inner_r - 3, raw_angle % 360)

        parts.append(
            f'<line x1="{tick_x:.1f}" y1="{tick_y:.1f}" x2="{px:.1f}" y2="{py:.1f}" '
            f'stroke="#30363D" stroke-width="0.5" stroke-dasharray="2,2"/>'
        )
        parts.append(
            f'<text x="{px:.1f}" y="{py:.1f}" fill="#E6EDF3" font-size="14" '
            f'text-anchor="middle" dominant-baseline="central" font-family="serif">{p.symbol}</text>'
        )

    for aspect in chart.aspects[:20]:
        p1 = next((p for p in chart.planets if p.name == aspect.planet1), None)
        p2 = next((p for p in chart.planets if p.name == aspect.planet2), None)
        if not p1 or not p2:
            continue

        a1 = (asc_offset - (p1.longitude - chart.ascendant)) % 360
        a2 = (asc_offset - (p2.longitude - chart.ascendant)) % 360

        x1, y1 = _polar_to_cartesian(cx, cy, aspect_r, a1)
        x2, y2 = _polar_to_cartesian(cx, cy, aspect_r, a2)

        color = ASPECT_COLORS.get(aspect.aspect_type, "#484F58")
        opacity = max(0.2, 1.0 - aspect.orb / 8.0)
        parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="0.8" opacity="{opacity:.2f}"/>'
        )

    parts.append("</svg>")
    return "\n".join(parts)
