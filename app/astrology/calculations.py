from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from math import fabs


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
    "Sun": "Солнце",
    "Moon": "Луна",
    "Mercury": "Меркурий",
    "Venus": "Венера",
    "Mars": "Марс",
    "Jupiter": "Юпитер",
    "Saturn": "Сатурн",
}

SWISSEPH_PLANETS = {
    "Sun": 0,
    "Moon": 1,
    "Mercury": 2,
    "Venus": 3,
    "Mars": 4,
    "Jupiter": 5,
    "Saturn": 6,
}

ASPECTS = {
    "соединение": 0,
    "секстиль": 60,
    "квадрат": 90,
    "тригон": 120,
    "оппозиция": 180,
}


@dataclass(frozen=True)
class PlanetPosition:
    key: str
    name: str
    longitude: float
    sign: str
    degree: float
    house: int | None = None


@dataclass(frozen=True)
class Aspect:
    planet_a: str
    planet_b: str
    aspect_type: str
    orb: float


@dataclass(frozen=True)
class NatalChart:
    birth_datetime: datetime
    birth_place: str
    latitude: float | None
    longitude: float | None
    planets: list[PlanetPosition]
    aspects: list[Aspect]


def calculate_natal_chart(
    birth_date: date,
    birth_time: time | None,
    birth_place: str,
    latitude: float | None,
    longitude: float | None,
) -> NatalChart:
    birth_datetime = datetime.combine(birth_date, birth_time or time(12, 0), tzinfo=UTC)
    planet_positions = _calculate_planets(birth_datetime)

    if latitude is not None and longitude is not None:
        planet_positions = [_with_equal_house(position, longitude) for position in planet_positions]

    return NatalChart(
        birth_datetime=birth_datetime,
        birth_place=birth_place,
        latitude=latitude,
        longitude=longitude,
        planets=planet_positions,
        aspects=calculate_aspects(planet_positions),
    )


def calculate_transits(target_date: date | None = None) -> list[PlanetPosition]:
    target_datetime = datetime.combine(target_date or date.today(), time(12, 0), tzinfo=UTC)
    return _calculate_planets(target_datetime)


def important_transits(natal: NatalChart, target_date: date | None = None) -> list[str]:
    transits = calculate_transits(target_date)
    messages: list[str] = []
    natal_by_key = {planet.key: planet for planet in natal.planets}

    for transit in transits:
        for natal_planet in natal_by_key.values():
            distance = _angular_distance(transit.longitude, natal_planet.longitude)
            for aspect_type, angle in ASPECTS.items():
                orb = abs(distance - angle)
                if orb <= 2.5:
                    messages.append(
                        f"{transit.name} образует {aspect_type} к натальной планете "
                        f"{natal_planet.name} (орб {orb:.1f}°)"
                    )

    return messages[:8]


def calculate_aspects(planets: list[PlanetPosition], orb_limit: float = 6.0) -> list[Aspect]:
    aspects: list[Aspect] = []
    for idx, planet_a in enumerate(planets):
        for planet_b in planets[idx + 1 :]:
            distance = _angular_distance(planet_a.longitude, planet_b.longitude)
            for aspect_type, angle in ASPECTS.items():
                orb = abs(distance - angle)
                if orb <= orb_limit:
                    aspects.append(
                        Aspect(
                            planet_a=planet_a.name,
                            planet_b=planet_b.name,
                            aspect_type=aspect_type,
                            orb=round(orb, 2),
                        )
                    )
                    break
    return aspects


def summarize_chart(chart: NatalChart) -> str:
    planets = ", ".join(
        f"{planet.name} в {planet.sign} {planet.degree:.1f}°"
        + (f" ({planet.house} дом)" if planet.house else "")
        for planet in chart.planets
    )
    aspects = "; ".join(
        f"{aspect.planet_a} — {aspect.aspect_type} — {aspect.planet_b} (орб {aspect.orb:.1f}°)"
        for aspect in chart.aspects[:10]
    )
    return f"Планеты: {planets}. Основные аспекты: {aspects or 'нет точных мажорных аспектов'}."


def chart_to_dict(chart: NatalChart) -> dict:
    return {
        "birth_datetime": chart.birth_datetime.isoformat(),
        "birth_place": chart.birth_place,
        "latitude": chart.latitude,
        "longitude": chart.longitude,
        "planets": [planet.__dict__ for planet in chart.planets],
        "aspects": [aspect.__dict__ for aspect in chart.aspects],
    }


def _calculate_planets(target_datetime: datetime) -> list[PlanetPosition]:
    try:
        return _calculate_with_swisseph(target_datetime)
    except Exception:
        return _calculate_with_simple_model(target_datetime)


def _calculate_with_swisseph(target_datetime: datetime) -> list[PlanetPosition]:
    import swisseph as swe

    julian_day = swe.julday(
        target_datetime.year,
        target_datetime.month,
        target_datetime.day,
        target_datetime.hour + target_datetime.minute / 60 + target_datetime.second / 3600,
    )
    positions: list[PlanetPosition] = []
    for key, swe_id in SWISSEPH_PLANETS.items():
        longitude = swe.calc_ut(julian_day, swe_id)[0][0] % 360
        positions.append(_planet_position(key, longitude))
    return positions


def _calculate_with_simple_model(target_datetime: datetime) -> list[PlanetPosition]:
    """Deterministic fallback for local development when ephemerides are missing."""

    day_number = target_datetime.toordinal() + target_datetime.hour / 24
    cycles = {
        "Sun": 365.25,
        "Moon": 27.32,
        "Mercury": 88.0,
        "Venus": 224.7,
        "Mars": 687.0,
        "Jupiter": 4332.6,
        "Saturn": 10759.0,
    }
    offsets = {
        "Sun": 280.0,
        "Moon": 120.0,
        "Mercury": 50.0,
        "Venus": 75.0,
        "Mars": 10.0,
        "Jupiter": 200.0,
        "Saturn": 310.0,
    }
    return [
        _planet_position(key, (offsets[key] + (day_number % cycle) / cycle * 360) % 360)
        for key, cycle in cycles.items()
    ]


def _planet_position(key: str, longitude: float) -> PlanetPosition:
    sign_index = int(longitude // 30)
    return PlanetPosition(
        key=key,
        name=PLANETS[key],
        longitude=round(longitude, 4),
        sign=SIGNS[sign_index],
        degree=round(longitude % 30, 2),
    )


def _with_equal_house(position: PlanetPosition, birthplace_longitude: float) -> PlanetPosition:
    adjusted = (position.longitude - birthplace_longitude) % 360
    house = int(adjusted // 30) + 1
    return PlanetPosition(
        key=position.key,
        name=position.name,
        longitude=position.longitude,
        sign=position.sign,
        degree=position.degree,
        house=house,
    )


def _angular_distance(longitude_a: float, longitude_b: float) -> float:
    distance = fabs((longitude_a - longitude_b) % 360)
    return min(distance, 360 - distance)
