import math
from typing import Any

from app.astrology.calculations import NatalChart, SIGN_EMOJI

PLANET_SYMBOLS = {
    "Солнце": "☉", "Луна": "☽", "Меркурий": "☿", "Венера": "♀",
    "Марс": "♂", "Юпитер": "♃", "Сатурн": "♄", "Уран": "♅",
    "Нептун": "♆", "Плутон": "♇",
}

ASPECT_COLORS = {
    "соединение": "#FFD700",
    "секстиль": "#4CAF50",
    "квадрат": "#F44336",
    "тригон": "#2196F3",
    "оппозиция": "#FF5722",
}

ZODIAC_SIGNS = [
    "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
    "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы",
]


class ChartRenderer:
    def __init__(self, size: int = 400) -> None:
        self.size = size
        self.cx = size / 2
        self.cy = size / 2
        self.outer_r = size / 2 - 10
        self.inner_r = self.outer_r * 0.75
        self.planet_r = self.outer_r * 0.55

    def _polar_to_cart(self, angle_deg: float, radius: float) -> tuple[float, float]:
        angle_rad = math.radians(90 - angle_deg)
        return self.cx + radius * math.cos(angle_rad), self.cy - radius * math.sin(angle_rad)

    def render_svg(self, chart: NatalChart) -> str:
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.size} {self.size}" '
            f'width="{self.size}" height="{self.size}">',
            '<defs>',
            '<radialGradient id="bg" cx="50%" cy="50%" r="50%">',
            '<stop offset="0%" stop-color="#1a1a2e"/>',
            '<stop offset="100%" stop-color="#0f0f23"/>',
            '</radialGradient>',
            '</defs>',
            f'<rect width="{self.size}" height="{self.size}" fill="url(#bg)" rx="8"/>',
        ]

        parts.append(
            f'<circle cx="{self.cx}" cy="{self.cy}" r="{self.outer_r}" '
            f'fill="none" stroke="#4a4a8a" stroke-width="2"/>'
        )
        parts.append(
            f'<circle cx="{self.cx}" cy="{self.cy}" r="{self.inner_r}" '
            f'fill="none" stroke="#3a3a6a" stroke-width="1"/>'
        )

        asc_offset = chart.ascendant
        for i, sign in enumerate(ZODIAC_SIGNS):
            start_angle = (i * 30 - asc_offset) % 360
            end_angle = ((i + 1) * 30 - asc_offset) % 360
            emoji = SIGN_EMOJI.get(sign, "")
            mid_angle = (start_angle + 15) % 360
            x, y = self._polar_to_cart(mid_angle, (self.outer_r + self.inner_r) / 2)
            parts.append(
                f'<text x="{x}" y="{y}" text-anchor="middle" dominant-baseline="middle" '
                f'font-size="14" fill="#c8c8e8">{emoji}</text>'
            )

        for i in range(12):
            angle = (i * 30 - asc_offset) % 360
            x1, y1 = self._polar_to_cart(angle, self.inner_r)
            x2, y2 = self._polar_to_cart(angle, self.outer_r)
            parts.append(
                f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#3a3a6a" stroke-width="0.5"/>'
            )

        for aspect in chart.aspects[:15]:
            p1 = next((p for p in chart.planets if p.name == aspect.planet1), None)
            p2 = next((p for p in chart.planets if p.name == aspect.planet2), None)
            if p1 and p2:
                a1 = (p1.longitude - asc_offset) % 360
                a2 = (p2.longitude - asc_offset) % 360
                x1, y1 = self._polar_to_cart(a1, self.planet_r)
                x2, y2 = self._polar_to_cart(a2, self.planet_r)
                color = ASPECT_COLORS.get(aspect.aspect_type, "#666")
                parts.append(
                    f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                    f'stroke="{color}" stroke-width="0.8" opacity="0.5"/>'
                )

        for planet in chart.planets:
            angle = (planet.longitude - asc_offset) % 360
            x, y = self._polar_to_cart(angle, self.planet_r)
            symbol = PLANET_SYMBOLS.get(planet.name, "●")
            color = "#FFD700" if planet.name == "Солнце" else "#E8E8F0"
            parts.append(
                f'<text x="{x}" y="{y}" text-anchor="middle" dominant-baseline="middle" '
                f'font-size="16" fill="{color}" font-weight="bold">{symbol}</text>'
            )

        parts.append(
            f'<text x="{self.cx}" y="{self.size - 15}" text-anchor="middle" '
            f'font-size="11" fill="#8888aa">ASC: {chart.ascendant_sign}</text>'
        )
        parts.append("</svg>")
        return "\n".join(parts)

    def render_json(self, chart: NatalChart) -> dict[str, Any]:
        from app.astrology.calculations import ChartCalculator
        calc = ChartCalculator()
        data = calc.chart_to_dict(chart)
        data["svg"] = self.render_svg(chart)
        return data
