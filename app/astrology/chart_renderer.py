from __future__ import annotations

from html import escape

from app.astrology.calculations import ChartData, polar_to_cartesian


SIGN_COLORS = [
    "#f97316",
    "#eab308",
    "#22c55e",
    "#06b6d4",
    "#8b5cf6",
    "#ec4899",
    "#14b8a6",
    "#f43f5e",
    "#84cc16",
    "#6366f1",
    "#0ea5e9",
    "#a855f7",
]

ASPECT_COLORS = {
    "conjunction": "#94a3b8",
    "opposition": "#ef4444",
    "trine": "#22c55e",
    "square": "#f97316",
    "sextile": "#0ea5e9",
}


def render_chart_svg(chart: ChartData, size: int = 720) -> str:
    center = size / 2
    outer_radius = size * 0.42
    inner_radius = size * 0.28
    planet_radius = size * 0.35

    sign_slices: list[str] = []
    for index, sign in enumerate(
        [
            "Aries",
            "Taurus",
            "Gemini",
            "Cancer",
            "Leo",
            "Virgo",
            "Libra",
            "Scorpio",
            "Sagittarius",
            "Capricorn",
            "Aquarius",
            "Pisces",
        ]
    ):
        start = index * 30
        end = start + 30
        x1, y1 = polar_to_cartesian(start, outer_radius, center, center)
        x2, y2 = polar_to_cartesian(end, outer_radius, center, center)
        ix1, iy1 = polar_to_cartesian(start, inner_radius, center, center)
        ix2, iy2 = polar_to_cartesian(end, inner_radius, center, center)
        large_arc_flag = 0
        sign_slices.append(
            f'<path d="M {ix1} {iy1} A {inner_radius} {inner_radius} 0 {large_arc_flag} 1 {ix2} {iy2} '
            f'L {x2} {y2} A {outer_radius} {outer_radius} 0 {large_arc_flag} 0 {x1} {y1} Z" '
            f'fill="{SIGN_COLORS[index]}" fill-opacity="0.16" stroke="#1f2937" stroke-width="1"/>'
        )
        label_x, label_y = polar_to_cartesian(start + 15, outer_radius - 24, center, center)
        sign_slices.append(
            f'<text x="{label_x}" y="{label_y}" text-anchor="middle" fill="#e2e8f0" '
            f'font-size="16" font-family="Inter, Arial, sans-serif">{escape(sign)}</text>'
        )

    aspect_lines: list[str] = []
    for aspect in chart.aspects:
        first = next(item for item in chart.planets if item.name == aspect.planet_a)
        second = next(item for item in chart.planets if item.name == aspect.planet_b)
        x1, y1 = polar_to_cartesian(first.longitude, inner_radius - 12, center, center)
        x2, y2 = polar_to_cartesian(second.longitude, inner_radius - 12, center, center)
        color = ASPECT_COLORS.get(aspect.aspect_type, "#94a3b8")
        aspect_lines.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{color}" stroke-width="2" stroke-opacity="0.7"/>'
        )

    planet_marks: list[str] = []
    for planet in chart.planets:
        x, y = polar_to_cartesian(planet.longitude, planet_radius, center, center)
        label_x, label_y = polar_to_cartesian(planet.longitude, planet_radius + 26, center, center)
        planet_marks.append(
            f'<circle cx="{x}" cy="{y}" r="7" fill="#f8fafc" stroke="#0f172a" stroke-width="2"/>'
        )
        planet_marks.append(
            f'<text x="{label_x}" y="{label_y}" text-anchor="middle" fill="#f8fafc" '
            f'font-size="14" font-weight="700" font-family="Inter, Arial, sans-serif">{escape(planet.name[:2])}</text>'
        )
    legend = "".join(
        f'<text x="40" y="{560 + idx * 24}" fill="#cbd5e1" font-size="15" '
        f'font-family="Inter, Arial, sans-serif">{escape(planet.name)} — {escape(planet.sign)} {planet.degree_in_sign:.1f}° / {planet.house} house</text>'
        for idx, planet in enumerate(chart.planets[:8])
    )

    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" '
        'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Natal chart">'
        '<rect width="100%" height="100%" rx="32" fill="#020617"/>'
        f'<circle cx="{center}" cy="{center}" r="{outer_radius}" fill="none" stroke="#334155" stroke-width="2"/>'
        f'<circle cx="{center}" cy="{center}" r="{inner_radius}" fill="none" stroke="#334155" stroke-width="2"/>'
        + "".join(sign_slices)
        + "".join(aspect_lines)
        + "".join(planet_marks)
        + f'<text x="{center}" y="56" text-anchor="middle" fill="#f8fafc" font-size="28" font-family="Inter, Arial, sans-serif" font-weight="700">{escape(chart.birth_place)}</text>'
        + f'<text x="{center}" y="88" text-anchor="middle" fill="#94a3b8" font-size="16" font-family="Inter, Arial, sans-serif">{escape(chart.birth_date)} {escape(chart.birth_time or "12:00")}</text>'
        + legend
        + "</svg>"
    )
