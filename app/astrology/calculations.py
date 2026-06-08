from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time
from itertools import combinations
from math import fabs

try:
    import swisseph as swe
except ImportError:  # pragma: no cover - runtime fallback when dependency is missing
    swe = None

PLANETS = {
    "Sun": 0,
    "Moon": 1,
    "Mercury": 2,
    "Venus": 3,
    "Mars": 4,
    "Jupiter": 5,
    "Saturn": 6,
    "Uranus": 7,
    "Neptune": 8,
    "Pluto": 9,
}

SIGNS = [
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

ASPECTS = [
    ("conjunction", 0, 8),
    ("sextile", 60, 4),
    ("square", 90, 6),
    ("trine", 120, 6),
    ("opposition", 180, 8),
]


@dataclass
class PlanetPosition:
    name: str
    longitude: float
    latitude: float
    sign: str
    degree_in_sign: float
    house: int


@dataclass
class Aspect:
    planet_a: str
    planet_b: str
    aspect_type: str
    exact_angle: float
    orb: float


@dataclass
class ChartData:
    planets: list[PlanetPosition]
    aspects: list[Aspect]
    ascendant: float
    houses: list[float]
    date: str
    time: str | None
    place: str

    def to_dict(self) -> dict:
        return {
            "planets": [asdict(p) for p in self.planets],
            "aspects": [asdict(a) for a in self.aspects],
            "ascendant": self.ascendant,
            "houses": self.houses,
            "date": self.date,
            "time": self.time,
            "place": self.place,
        }


def _safe_birth_time(birth_time: time | None) -> time:
    return birth_time or time(hour=12, minute=0)


def _zodiac_sign(longitude: float) -> tuple[str, float]:
    normalized = longitude % 360
    sign_index = int(normalized // 30)
    return SIGNS[sign_index], normalized % 30


def _planet_house(longitude: float, ascendant: float) -> int:
    shifted = (longitude - ascendant) % 360
    return int(shifted // 30) + 1


def _fallback_longitude(base: float, idx: int) -> float:
    return (base + idx * 33.3) % 360


def _calculate_planets(julian_day: float, ascendant: float) -> list[PlanetPosition]:
    planets: list[PlanetPosition] = []
    for i, (name, code) in enumerate(PLANETS.items()):
        if swe is None:
            longitude = _fallback_longitude(julian_day * 10, i)
            latitude = 0.0
        else:
            values, _ = swe.calc_ut(julian_day, code)
            longitude = float(values[0])
            latitude = float(values[1])

        sign, degree_in_sign = _zodiac_sign(longitude)
        planets.append(
            PlanetPosition(
                name=name,
                longitude=longitude,
                latitude=latitude,
                sign=sign,
                degree_in_sign=degree_in_sign,
                house=_planet_house(longitude, ascendant),
            )
        )
    return planets


def _calculate_aspects(planets: list[PlanetPosition]) -> list[Aspect]:
    aspects: list[Aspect] = []
    for p1, p2 in combinations(planets, 2):
        diff = fabs(p1.longitude - p2.longitude)
        angle = min(diff, 360 - diff)
        for aspect_name, target, orb_limit in ASPECTS:
            orb = fabs(angle - target)
            if orb <= orb_limit:
                aspects.append(
                    Aspect(
                        planet_a=p1.name,
                        planet_b=p2.name,
                        aspect_type=aspect_name,
                        exact_angle=round(angle, 2),
                        orb=round(orb, 2),
                    )
                )
                break
    return aspects


def calculate_natal_chart(
    birth_date: date,
    birth_time: time | None,
    latitude: float | None,
    longitude: float | None,
    place: str,
) -> ChartData:
    t = _safe_birth_time(birth_time)
    dt = datetime.combine(birth_date, t)
    lat = latitude if latitude is not None else 55.7558
    lon = longitude if longitude is not None else 37.6176

    if swe is None:
        julian_day = dt.timestamp() / 86400 + 2440587.5
        ascendant = (julian_day * 13.0) % 360
        houses = [float((ascendant + i * 30) % 360) for i in range(12)]
    else:
        julian_day = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60)
        house_cusps, ascmc = swe.houses_ex(julian_day, lat, lon, b"P")
        ascendant = float(ascmc[0])
        houses = [float(cusp) for cusp in house_cusps[:12]]

    planets = _calculate_planets(julian_day, ascendant)
    aspects = _calculate_aspects(planets)
    return ChartData(
        planets=planets,
        aspects=aspects,
        ascendant=round(ascendant, 2),
        houses=[round(h, 2) for h in houses],
        date=birth_date.isoformat(),
        time=t.strftime("%H:%M") if birth_time else None,
        place=place,
    )


def calculate_daily_transits(
    natal_chart: ChartData,
    transit_date: date,
    latitude: float | None,
    longitude: float | None,
) -> list[Aspect]:
    transit_chart = calculate_natal_chart(
        birth_date=transit_date,
        birth_time=time(hour=12, minute=0),
        latitude=latitude,
        longitude=longitude,
        place="Current transits",
    )
    transits: list[Aspect] = []
    natal_planets = {p.name: p for p in natal_chart.planets}
    for t_planet in transit_chart.planets:
        for n_planet in natal_planets.values():
            diff = fabs(t_planet.longitude - n_planet.longitude)
            angle = min(diff, 360 - diff)
            for aspect_name, target, orb_limit in ASPECTS:
                orb = fabs(angle - target)
                if orb <= orb_limit:
                    transits.append(
                        Aspect(
                            planet_a=f"Transit {t_planet.name}",
                            planet_b=f"Natal {n_planet.name}",
                            aspect_type=aspect_name,
                            exact_angle=round(angle, 2),
                            orb=round(orb, 2),
                        )
                    )
                    break
    return transits[:20]


def compatibility_score(first: ChartData, second: ChartData) -> tuple[int, list[str]]:
    score = 50
    highlights: list[str] = []
    second_map = {p.name: p for p in second.planets}
    for p in first.planets:
        p2 = second_map.get(p.name)
        if not p2:
            continue
        diff = fabs(p.longitude - p2.longitude)
        angle = min(diff, 360 - diff)
        if angle <= 10:
            score += 4
            highlights.append(f"{p.name}: сильный резонанс энергий")
        elif 110 <= angle <= 130:
            score += 3
            highlights.append(f"{p.name}: гармоничный тригон")
        elif 80 <= angle <= 100:
            score -= 2
            highlights.append(f"{p.name}: зона напряжения, важен диалог")
        elif angle >= 170:
            score -= 3
            highlights.append(f"{p.name}: полярность взглядов, нужен баланс")
    score = max(1, min(score, 99))
    return score, highlights[:6]
