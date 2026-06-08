from math import cos, radians, sin

from app.astrology.calculations import ChartData

ASPECT_COLORS = {
    "conjunction": "#f59e0b",
    "sextile": "#10b981",
    "square": "#ef4444",
    "trine": "#3b82f6",
    "opposition": "#8b5cf6",
}


def _coord(center: float, radius: float, degree: float) -> tuple[float, float]:
    # SVG uses 0 deg to the right, while astrological charts are drawn from top clockwise.
    angle = radians(degree - 90)
    return center + radius * cos(angle), center + radius * sin(angle)


def render_natal_chart_svg(chart: ChartData, size: int = 720) -> str:
    center = size / 2
    outer_radius = size * 0.42
    planet_radius = size * 0.32

    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">',
        '<rect width="100%" height="100%" fill="#0b1020"/>',
        f'<circle cx="{center}" cy="{center}" r="{outer_radius}" fill="none" stroke="#475569" stroke-width="2"/>',
        f'<circle cx="{center}" cy="{center}" r="{planet_radius}" fill="none" stroke="#334155" stroke-width="1"/>',
    ]

    for i in range(12):
        cusp = chart.houses[i] if i < len(chart.houses) else (chart.ascendant + i * 30) % 360
        x, y = _coord(center, outer_radius, cusp)
        lines.append(
            f'<line x1="{center}" y1="{center}" x2="{x:.2f}" y2="{y:.2f}" stroke="#1e293b" stroke-width="1"/>'
        )

    planet_points: dict[str, tuple[float, float]] = {}
    for planet in chart.planets:
        x, y = _coord(center, planet_radius, planet.longitude)
        planet_points[planet.name] = (x, y)
        label = f"{planet.name[:2]} {planet.sign[:3]} {planet.degree_in_sign:.1f}°"
        lines.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="5" fill="#f8fafc"/>')
        lines.append(
            f'<text x="{x + 8:.2f}" y="{y - 8:.2f}" font-size="12" fill="#e2e8f0" font-family="Arial">{label}</text>'
        )

    for aspect in chart.aspects[:40]:
        p1 = planet_points.get(aspect.planet_a)
        p2 = planet_points.get(aspect.planet_b)
        if not p1 or not p2:
            continue
        color = ASPECT_COLORS.get(aspect.aspect_type, "#64748b")
        lines.append(
            f'<line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" '
            f'stroke="{color}" stroke-opacity="0.5" stroke-width="1"/>'
        )

    lines.append(
        f'<text x="{center}" y="{size - 20}" text-anchor="middle" font-size="14" fill="#cbd5e1" '
        f'font-family="Arial">Stellarium AI · {chart.place} · {chart.date}</text>'
    )
    lines.append("</svg>")
    return "\n".join(lines)
