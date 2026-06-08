from html import escape
from math import cos, pi, sin

from app.astrology.calculations import NatalChart


PLANET_GLYPHS = {
    "Sun": "☉",
    "Moon": "☽",
    "Mercury": "☿",
    "Venus": "♀",
    "Mars": "♂",
    "Jupiter": "♃",
    "Saturn": "♄",
}


def render_chart_svg(chart: NatalChart, size: int = 640) -> str:
    center = size / 2
    outer_radius = size * 0.42
    inner_radius = size * 0.30
    planet_radius = size * 0.36

    parts = [
        f'<svg viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg" role="img">',
        '<defs><style>text{font-family:Inter,Arial,sans-serif}.label{font-size:13px;fill:#f8f5ff}'
        '.planet{font-size:24px;fill:#f8f5ff}.line{stroke:#8b5cf6;stroke-width:1;opacity:.35}'
        '.aspect{stroke:#fbbf24;stroke-width:1;opacity:.45}.ring{fill:none;stroke:#f8f5ff;stroke-width:2;opacity:.85}'
        '</style></defs>',
        f'<circle cx="{center}" cy="{center}" r="{outer_radius}" fill="#17112b"/>',
        f'<circle class="ring" cx="{center}" cy="{center}" r="{outer_radius}"/>',
        f'<circle class="ring" cx="{center}" cy="{center}" r="{inner_radius}"/>',
    ]

    for idx in range(12):
        angle = _angle(idx * 30)
        x1, y1 = _point(center, outer_radius, angle)
        x2, y2 = _point(center, inner_radius, angle)
        label_x, label_y = _point(center, outer_radius + 24, _angle(idx * 30 + 15))
        parts.append(f'<line class="line" x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}"/>')
        parts.append(
            f'<text class="label" x="{label_x:.2f}" y="{label_y:.2f}" text-anchor="middle" '
            f'dominant-baseline="middle">{idx + 1}</text>'
        )

    planet_points: dict[str, tuple[float, float]] = {}
    for planet in chart.planets:
        x, y = _point(center, planet_radius, _angle(planet.longitude))
        planet_points[planet.name] = (x, y)
        glyph = escape(PLANET_GLYPHS.get(planet.key, planet.name[:1]))
        parts.append(
            f'<text class="planet" x="{x:.2f}" y="{y:.2f}" text-anchor="middle" '
            f'dominant-baseline="middle"><title>{escape(planet.name)} в {escape(planet.sign)}</title>{glyph}</text>'
        )

    for aspect in chart.aspects[:16]:
        point_a = planet_points.get(aspect.planet_a)
        point_b = planet_points.get(aspect.planet_b)
        if point_a and point_b:
            parts.append(
                f'<line class="aspect" x1="{point_a[0]:.2f}" y1="{point_a[1]:.2f}" '
                f'x2="{point_b[0]:.2f}" y2="{point_b[1]:.2f}"><title>'
                f'{escape(aspect.planet_a)} {escape(aspect.aspect_type)} {escape(aspect.planet_b)}</title></line>'
            )

    parts.append(
        f'<text class="label" x="{center}" y="{center}" text-anchor="middle" dominant-baseline="middle">'
        f'{escape(chart.birth_place)}</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


def _angle(longitude: float) -> float:
    return (longitude - 90) * pi / 180


def _point(center: float, radius: float, angle: float) -> tuple[float, float]:
    return center + radius * cos(angle), center + radius * sin(angle)
