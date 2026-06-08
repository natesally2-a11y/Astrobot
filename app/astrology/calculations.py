from __future__ import annotations

import math
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.astrology.schemas import Aspect, BirthProfile, NatalChart, PlanetPosition, Transit

try:
    import swisseph as swe
except Exception:  # pragma: no cover - used only if the native package is unavailable
    swe = None


SIGNS = [
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

PLANETS = {
    "sun": ("Солнце", getattr(swe, "SUN", 0) if swe else 0),
    "moon": ("Луна", getattr(swe, "MOON", 1) if swe else 1),
    "mercury": ("Меркурий", getattr(swe, "MERCURY", 2) if swe else 2),
    "venus": ("Венера", getattr(swe, "VENUS", 3) if swe else 3),
    "mars": ("Марс", getattr(swe, "MARS", 4) if swe else 4),
    "jupiter": ("Юпитер", getattr(swe, "JUPITER", 5) if swe else 5),
    "saturn": ("Сатурн", getattr(swe, "SATURN", 6) if swe else 6),
    "uranus": ("Уран", getattr(swe, "URANUS", 7) if swe else 7),
    "neptune": ("Нептун", getattr(swe, "NEPTUNE", 8) if swe else 8),
    "pluto": ("Плутон", getattr(swe, "PLUTO", 9) if swe else 9),
}

ASPECTS = {
    "соединение": 0,
    "секстиль": 60,
    "квадрат": 90,
    "тригон": 120,
    "оппозиция": 180,
}


def normalize_longitude(value: float) -> float:
    return value % 360


def angle_distance(a: float, b: float) -> float:
    diff = abs(normalize_longitude(a) - normalize_longitude(b))
    return min(diff, 360 - diff)


def sign_for_longitude(longitude: float) -> tuple[str, int, float]:
    normalized = normalize_longitude(longitude)
    sign_index = int(normalized // 30)
    degree = normalized - sign_index * 30
    return SIGNS[sign_index], sign_index, degree


def _local_birth_datetime(profile: BirthProfile) -> datetime:
    birth_time = profile.birth_time or time(hour=12)
    local = datetime.combine(profile.birth_date, birth_time)
    if not profile.timezone:
        return local.replace(tzinfo=timezone.utc)
    try:
        return local.replace(tzinfo=ZoneInfo(profile.timezone))
    except ZoneInfoNotFoundError:
        return local.replace(tzinfo=timezone.utc)


def _julian_day(moment: datetime) -> float:
    utc = moment.astimezone(timezone.utc)
    hour = utc.hour + utc.minute / 60 + utc.second / 3600
    if swe:
        return float(swe.julday(utc.year, utc.month, utc.day, hour))
    ordinal = date(utc.year, utc.month, utc.day).toordinal()
    return float(ordinal + 1721424.5 + hour / 24)


def _fallback_longitude(julian_day: float, planet_index: int) -> float:
    speed = [0.9856, 13.1764, 4.0923, 1.6021, 0.524, 0.0831, 0.0335, 0.0117, 0.006, 0.004][planet_index]
    seed = (julian_day - 2451545.0) * speed + planet_index * 37.77
    return normalize_longitude(seed)


def _planet_longitude(julian_day: float, planet_id: int, fallback_index: int) -> float:
    if swe is None:
        return _fallback_longitude(julian_day, fallback_index)
    try:
        result, _flags = swe.calc_ut(julian_day, planet_id)
        return normalize_longitude(float(result[0]))
    except Exception:
        return _fallback_longitude(julian_day, fallback_index)


def _calculate_houses(julian_day: float, latitude: float | None, longitude: float | None) -> list[float]:
    if swe is None or latitude is None or longitude is None:
        return []
    try:
        houses, _ascmc = swe.houses_ex(julian_day, float(latitude), float(longitude), b"P")
        return [normalize_longitude(float(cusp)) for cusp in houses[:12]]
    except Exception:
        return []


def _house_for_longitude(longitude: float, houses: list[float]) -> int | None:
    if len(houses) != 12:
        return None
    for index, start in enumerate(houses):
        end = houses[(index + 1) % 12]
        span = (end - start) % 360
        offset = (normalize_longitude(longitude) - start) % 360
        if offset <= span:
            return index + 1
    return None


def _calculate_aspects(planets: list[PlanetPosition], orb_limit: float = 6.0) -> list[Aspect]:
    aspects: list[Aspect] = []
    for left_index, left in enumerate(planets):
        for right in planets[left_index + 1 :]:
            distance = angle_distance(left.longitude, right.longitude)
            for name, exact_angle in ASPECTS.items():
                orb = abs(distance - exact_angle)
                if orb <= orb_limit:
                    aspects.append(
                        Aspect(
                            planet_a=left.label,
                            planet_b=right.label,
                            aspect=name,
                            angle=exact_angle,
                            orb=round(orb, 2),
                        )
                    )
                    break
    return sorted(aspects, key=lambda item: item.orb)


def build_natal_chart(profile: BirthProfile) -> NatalChart:
    moment = _local_birth_datetime(profile)
    julian_day = _julian_day(moment)
    houses = _calculate_houses(julian_day, profile.latitude, profile.longitude)

    planets: list[PlanetPosition] = []
    for index, (key, (label, planet_id)) in enumerate(PLANETS.items()):
        longitude = _planet_longitude(julian_day, planet_id, index)
        sign, sign_index, degree = sign_for_longitude(longitude)
        planets.append(
            PlanetPosition(
                planet=key,
                label=label,
                longitude=longitude,
                sign=sign,
                sign_index=sign_index,
                degree=round(degree, 2),
                house=_house_for_longitude(longitude, houses),
            )
        )

    return NatalChart(
        profile=profile,
        calculated_for=moment,
        planets=planets,
        aspects=_calculate_aspects(planets),
        houses=houses,
    )


def calculate_transits(chart: NatalChart, target_date: date | None = None) -> list[Transit]:
    transit_profile = BirthProfile(
        birth_date=target_date or date.today(),
        birth_time=time(hour=12),
        birth_place="Текущие транзиты",
        latitude=chart.profile.latitude,
        longitude=chart.profile.longitude,
        timezone=chart.profile.timezone,
    )
    transit_chart = build_natal_chart(transit_profile)
    transits: list[Transit] = []
    natal_planets = {planet.label: planet for planet in chart.planets}

    for transit_planet in transit_chart.planets:
        for natal_planet in natal_planets.values():
            distance = angle_distance(transit_planet.longitude, natal_planet.longitude)
            for aspect_name, exact_angle in ASPECTS.items():
                orb = abs(distance - exact_angle)
                if orb <= 2.5:
                    transits.append(
                        Transit(
                            transit_planet=transit_planet.label,
                            natal_planet=natal_planet.label,
                            aspect=aspect_name,
                            orb=round(orb, 2),
                        )
                    )
                    break
    return sorted(transits, key=lambda item: item.orb)[:12]


def describe_chart_short(chart: NatalChart) -> str:
    sun = next((planet for planet in chart.planets if planet.planet == "sun"), None)
    moon = next((planet for planet in chart.planets if planet.planet == "moon"), None)
    asc_house = "не рассчитан"
    if chart.houses:
        sign, _idx, degree = sign_for_longitude(chart.houses[0])
        asc_house = f"{sign} {degree:.1f}°"
    core = []
    if sun:
        core.append(f"Солнце в {sun.sign}")
    if moon:
        core.append(f"Луна в {moon.sign}")
    core.append(f"Асцендент: {asc_house}")
    return ", ".join(core)


def compatibility_by_signs(left: NatalChart, right: NatalChart) -> str:
    elements = {
        0: "огонь",
        1: "земля",
        2: "воздух",
        3: "вода",
        4: "огонь",
        5: "земля",
        6: "воздух",
        7: "вода",
        8: "огонь",
        9: "земля",
        10: "воздух",
        11: "вода",
    }
    left_sun = next(planet for planet in left.planets if planet.planet == "sun")
    right_sun = next(planet for planet in right.planets if planet.planet == "sun")
    left_element = elements[left_sun.sign_index]
    right_element = elements[right_sun.sign_index]
    if left_element == right_element:
        tone = "легкое взаимопонимание и сходный жизненный ритм"
    elif {left_element, right_element} in [{"огонь", "воздух"}, {"земля", "вода"}]:
        tone = "естественную поддержку и хороший потенциал роста"
    else:
        tone = "яркое притяжение, которому нужны договоренности и уважение границ"
    return (
        f"Солнце первого партнера в знаке {left_sun.sign}, второго — в знаке {right_sun.sign}. "
        f"Связка элементов {left_element} + {right_element} дает {tone}."
    )


def planet_table(chart: NatalChart) -> list[dict[str, str | int | float | None]]:
    return [
        {
            "planet": planet.planet,
            "label": planet.label,
            "sign": planet.sign,
            "degree": planet.degree,
            "house": planet.house,
            "longitude": round(planet.longitude, 4),
        }
        for planet in chart.planets
    ]
