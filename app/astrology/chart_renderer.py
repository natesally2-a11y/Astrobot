from __future__ import annotations

from math import cos, radians, sin

SIGN_SYMBOLS = ['Ar', 'Ta', 'Ge', 'Ca', 'Le', 'Vi', 'Li', 'Sc', 'Sg', 'Cp', 'Aq', 'Pi']


def polar(cx: float, cy: float, radius: float, degrees: float) -> tuple[float, float]:
    angle = radians(degrees - 90)
    return cx + radius * cos(angle), cy + radius * sin(angle)


def render_chart_svg(chart: dict, size: int = 680) -> str:
    cx = cy = size / 2
    outer = size * 0.42
    inner = size * 0.28
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" role="img" aria-label="Natal chart">',
        '<rect width="100%" height="100%" fill="#0f172a" rx="24"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{outer}" fill="#111827" stroke="#38bdf8" stroke-width="3"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{inner}" fill="#020617" stroke="#475569" stroke-width="2"/>',
    ]
    for index in range(12):
        degree = index * 30
        x1, y1 = polar(cx, cy, inner, degree)
        x2, y2 = polar(cx, cy, outer, degree)
        tx, ty = polar(cx, cy, outer + 28, degree + 15)
        lines.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#334155" stroke-width="2"/>')
        lines.append(f'<text x="{tx:.2f}" y="{ty:.2f}" fill="#e2e8f0" font-size="18" text-anchor="middle" dominant-baseline="middle">{SIGN_SYMBOLS[index]}</text>')
    for planet in chart['planets']:
        px, py = polar(cx, cy, (outer + inner) / 2, planet['longitude'])
        lines.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="7" fill="#f97316"/>')
        lines.append(f'<text x="{px:.2f}" y="{py - 16:.2f}" fill="#f8fafc" font-size="13" text-anchor="middle">{planet["name"][:3]}</text>')
    lines.append(f'<text x="{cx}" y="46" fill="#f8fafc" font-size="28" text-anchor="middle">Stellarium AI Natal Chart</text>')
    lines.append('</svg>')
    return ''.join(lines)
