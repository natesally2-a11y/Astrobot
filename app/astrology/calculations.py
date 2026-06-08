from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timezone
from itertools import combinations
from zoneinfo import ZoneInfo

import swisseph as swe

PLANETS = {
    'Sun': swe.SUN,
    'Moon': swe.MOON,
    'Mercury': swe.MERCURY,
    'Venus': swe.VENUS,
    'Mars': swe.MARS,
    'Jupiter': swe.JUPITER,
    'Saturn': swe.SATURN,
    'Uranus': swe.URANUS,
    'Neptune': swe.NEPTUNE,
    'Pluto': swe.PLUTO,
}

SIGNS = [
    'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
]

ASPECTS = {
    0: 'Conjunction',
    60: 'Sextile',
    90: 'Square',
    120: 'Trine',
    180: 'Opposition',
}


@dataclass(slots=True)
class BirthInfo:
    birth_date: date
    birth_time: time | None
    latitude: float
    longitude: float
    timezone: str
    birth_place: str
    is_time_approximate: bool = False


@dataclass(slots=True)
class PlanetPosition:
    name: str
    longitude: float
    sign: str
    degree_in_sign: float
    house: int


def normalize_angle(angle: float) -> float:
    return angle % 360


def angular_distance(a: float, b: float) -> float:
    distance = abs(normalize_angle(a) - normalize_angle(b))
    return min(distance, 360 - distance)


def house_for_longitude(longitude: float, cusps: list[float]) -> int:
    extended = list(cusps) + [cusps[0] + 360]
    longitude = normalize_angle(longitude)
    for index in range(12):
        start = normalize_angle(extended[index])
        end = normalize_angle(extended[index + 1])
        if start <= end and start <= longitude < end:
            return index + 1
        if start > end and (longitude >= start or longitude < end):
            return index + 1
    return 12


def _to_utc_datetime(info: BirthInfo) -> datetime:
    hour = info.birth_time.hour if info.birth_time else 12
    minute = info.birth_time.minute if info.birth_time else 0
    local = datetime(
        info.birth_date.year,
        info.birth_date.month,
        info.birth_date.day,
        hour,
        minute,
        tzinfo=ZoneInfo(info.timezone),
    )
    return local.astimezone(timezone.utc)


def _julian_day(dt: datetime) -> float:
    hour_float = dt.hour + dt.minute / 60 + dt.second / 3600
    return swe.julday(dt.year, dt.month, dt.day, hour_float)


def calculate_natal_chart(info: BirthInfo) -> dict:
    utc_dt = _to_utc_datetime(info)
    jd = _julian_day(utc_dt)
    cusps, ascmc = swe.houses(jd, info.latitude, info.longitude, b'P')
    positions = []
    for planet_name, planet_id in PLANETS.items():
        longitude = swe.calc_ut(jd, planet_id)[0][0]
        sign_index = int(longitude // 30)
        positions.append(
            PlanetPosition(
                name=planet_name,
                longitude=round(longitude, 4),
                sign=SIGNS[sign_index],
                degree_in_sign=round(longitude % 30, 2),
                house=house_for_longitude(longitude, list(cusps)),
            )
        )
    aspects = []
    for first, second in combinations(positions, 2):
        distance = angular_distance(first.longitude, second.longitude)
        for angle, label in ASPECTS.items():
            orb = abs(distance - angle)
            if orb <= 6:
                aspects.append(
                    {
                        'between': [first.name, second.name],
                        'aspect': label,
                        'exact_angle': angle,
                        'orb': round(orb, 2),
                    }
                )
                break
    return {
        'birth_place': info.birth_place,
        'birth_datetime_utc': utc_dt.isoformat(),
        'timezone': info.timezone,
        'is_time_approximate': info.is_time_approximate,
        'ascendant': round(ascmc[0], 2),
        'midheaven': round(ascmc[1], 2),
        'houses': [round(value, 2) for value in cusps],
        'planets': [asdict(position) for position in positions],
        'aspects': aspects,
    }


def calculate_daily_transits(chart: dict, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    jd = _julian_day(now)
    natal_positions = {planet['name']: planet for planet in chart['planets']}
    transit_positions = {}
    important = []
    for planet_name, planet_id in PLANETS.items():
        longitude = swe.calc_ut(jd, planet_id)[0][0]
        sign = SIGNS[int(longitude // 30)]
        transit_positions[planet_name] = {
            'longitude': round(longitude, 4),
            'sign': sign,
            'degree_in_sign': round(longitude % 30, 2),
        }
        if planet_name in {'Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn'}:
            natal_sun = natal_positions['Sun']
            distance = angular_distance(longitude, natal_sun['longitude'])
            for angle, label in ASPECTS.items():
                orb = abs(distance - angle)
                if orb <= 3:
                    important.append(
                        {
                            'transit_planet': planet_name,
                            'target': 'Sun',
                            'aspect': label,
                            'orb': round(orb, 2),
                        }
                    )
                    break
    return {
        'generated_at': now.isoformat(),
        'positions': transit_positions,
        'important_transits': important[:8],
    }


def calculate_compatibility(first_chart: dict, second_chart: dict, second_name: str = 'Partner') -> dict:
    first_planets = {planet['name']: planet for planet in first_chart['planets']}
    second_planets = {planet['name']: planet for planet in second_chart['planets']}
    relationships = []
    score = 50
    for source in ('Sun', 'Moon', 'Venus', 'Mars'):
        for target in ('Sun', 'Moon', 'Venus', 'Mars'):
            distance = angular_distance(first_planets[source]['longitude'], second_planets[target]['longitude'])
            for angle, label in ASPECTS.items():
                orb = abs(distance - angle)
                if orb <= 6:
                    delta = {0: 8, 60: 6, 90: -5, 120: 9, 180: -3}[angle]
                    score += delta
                    relationships.append(
                        {
                            'between': [source, f'{second_name} {target}'],
                            'aspect': label,
                            'orb': round(orb, 2),
                            'impact': delta,
                        }
                    )
                    break
    score = max(1, min(99, score))
    return {'score': score, 'aspects': relationships[:12]}


def summarize_chart(chart: dict) -> str:
    planets = {planet['name']: planet for planet in chart['planets']}
    return (
        f"Sun in {planets['Sun']['sign']} house {planets['Sun']['house']}, "
        f"Moon in {planets['Moon']['sign']} house {planets['Moon']['house']}, "
        f"Ascendant {chart['ascendant']:.2f}."
    )
