from __future__ import annotations

import math

from app.astrology.calculations import NatalChart


def render_chart_svg(chart: NatalChart) -> str:
    center_x, center_y = 250, 250
    radius = 200
    text_radius = 170
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="500" height="500" viewBox="0 0 500 500">',
        '<rect x="0" y="0" width="500" height="500" fill="#0b1020"/>',
        f'<circle cx="{center_x}" cy="{center_y}" r="{radius}" fill="none" stroke="#7d8cff" stroke-width="2"/>',
        '<text x="250" y="35" fill="#ffffff" text-anchor="middle" font-size="18">Stellarium AI Natal Chart</text>',
    ]

    for i in range(12):
        angle = math.radians(i * 30 - 90)
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        lines.append(f'<line x1="{center_x}" y1="{center_y}" x2="{x:.2f}" y2="{y:.2f}" stroke="#2f3b6a" />')

    for position in chart.planets:
        angle = math.radians(position.longitude - 90)
        x = center_x + text_radius * math.cos(angle)
        y = center_y + text_radius * math.sin(angle)
        lines.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="#ffd166"/>')
        lines.append(
            f'<text x="{x:.2f}" y="{(y - 8):.2f}" fill="#f8f9ff" text-anchor="middle" font-size="11">'
            f"{position.name}</text>"
        )

    lines.append(
        f'<text x="250" y="470" fill="#d0d7ff" text-anchor="middle" font-size="14">'
        f"Солнце: {chart.sun_sign}</text>"
    )
    lines.append("</svg>")
    return "".join(lines)

