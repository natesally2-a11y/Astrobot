from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from hashlib import sha256
from typing import Optional

try:
    import swisseph as swe
except ImportError:  # pragma: no cover - fallback path for environments without swisseph
    swe = None


ZODIAC_SIGNS = [
    "Овен",
    "Телец",
    "Близнецы",
    "Рак",
    "Лев",
    "Дева",
    "Весы",
    "Скорпион",
    "Стрелец",
    "Козерог",
    "Водолей",
    "Рыбы",
]

PLANETS = ["Солнце", "Луна", "Меркурий", "Венера", "Марс", "Юпитер", "Сатурн"]


@dataclass
class PlanetPosition:
    name: str
    longitude: float
    sign: str
    house: int


@dataclass
class NatalChart:
    generated_at: datetime
    sun_sign: str
    planets: list[PlanetPosition]


def _sign_by_longitude(longitude: float) -> str:
    return ZODIAC_SIGNS[int(longitude // 30) % 12]


def _fallback_position(seed: str, planet: str) -> tuple[float, int]:
    digest = sha256(f"{seed}:{planet}".encode("utf-8")).hexdigest()
    longitude = int(digest[:8], 16) % 360
    house = int(digest[8:10], 16) % 12 + 1
    return float(longitude), house


def _to_decimal_hour(birth_time: Optional[time]) -> float:
    if not birth_time:
        return 12.0
    return birth_time.hour + birth_time.minute / 60.0 + birth_time.second / 3600.0


def build_natal_chart(
    birth_date: date,
    birth_time: Optional[time],
    latitude: Optional[float],
    longitude: Optional[float],
) -> NatalChart:
    decimal_hour = _to_decimal_hour(birth_time)
    generated_at = datetime.utcnow()
    seed = f"{birth_date.isoformat()}:{decimal_hour:.2f}:{latitude}:{longitude}"
    planets: list[PlanetPosition] = []

    if swe is not None and latitude is not None and longitude is not None:
        julian_day = swe.julday(birth_date.year, birth_date.month, birth_date.day, decimal_hour)
        house_cusps, _ = swe.houses(julian_day, latitude, longitude, b"P")
        planet_map = {
            "Солнце": swe.SUN,
            "Луна": swe.MOON,
            "Меркурий": swe.MERCURY,
            "Венера": swe.VENUS,
            "Марс": swe.MARS,
            "Юпитер": swe.JUPITER,
            "Сатурн": swe.SATURN,
        }
        for name, code in planet_map.items():
            lon = float(swe.calc_ut(julian_day, code)[0][0])
            house = 1
            for idx, cusp in enumerate(house_cusps, start=1):
                next_cusp = house_cusps[idx % 12]
                if cusp <= lon < next_cusp:
                    house = idx
                    break
            planets.append(PlanetPosition(name=name, longitude=lon, sign=_sign_by_longitude(lon), house=house))
    else:
        for planet in PLANETS:
            lon, house = _fallback_position(seed, planet)
            planets.append(PlanetPosition(name=planet, longitude=lon, sign=_sign_by_longitude(lon), house=house))

    sun_sign = next(p.sign for p in planets if p.name == "Солнце")
    return NatalChart(generated_at=generated_at, sun_sign=sun_sign, planets=planets)


def daily_transit_summary(chart: NatalChart, day: date) -> str:
    digest = sha256(f"{chart.sun_sign}:{day.isoformat()}".encode("utf-8")).hexdigest()
    mood_index = int(digest[:2], 16) % 3
    focus = ["отношения", "карьера", "восстановление энергии"][mood_index]
    return f"Сегодня акцент на сфере «{focus}». Действуйте осознанно и без спешки."


def compatibility_snapshot(chart_a: NatalChart, chart_b: NatalChart) -> str:
    raw_score = (ZODIAC_SIGNS.index(chart_a.sun_sign) - ZODIAC_SIGNS.index(chart_b.sun_sign)) % 12
    score = 100 - min(raw_score, 12 - raw_score) * 8
    if score >= 75:
        tone = "очень гармоничная пара"
    elif score >= 55:
        tone = "интересный союз с потенциалом"
    else:
        tone = "контрастный союз, требующий диалога"
    return f"Солнечная совместимость: {score}%. Это {tone}."

