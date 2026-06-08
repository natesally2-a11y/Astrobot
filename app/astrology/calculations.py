"""Astrological calculations using Swiss Ephemeris (pyswisseph)."""

from dataclasses import dataclass, field
from datetime import datetime, date, time
from decimal import Decimal
import math

import swisseph as swe

ZODIAC_SIGNS = [
    "Овен", "Телец", "Близнецы", "Рак",
    "Лев", "Дева", "Весы", "Скорпион",
    "Стрелец", "Козерог", "Водолей", "Рыбы",
]

ZODIAC_SIGNS_EN = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

ZODIAC_SYMBOLS = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]

PLANET_NAMES = {
    swe.SUN: "Солнце",
    swe.MOON: "Луна",
    swe.MERCURY: "Меркурий",
    swe.VENUS: "Венера",
    swe.MARS: "Марс",
    swe.JUPITER: "Юпитер",
    swe.SATURN: "Сатурн",
    swe.URANUS: "Уран",
    swe.NEPTUNE: "Нептун",
    swe.PLUTO: "Плутон",
    swe.MEAN_NODE: "Сев. узел",
}

PLANET_SYMBOLS = {
    swe.SUN: "☉",
    swe.MOON: "☽",
    swe.MERCURY: "☿",
    swe.VENUS: "♀",
    swe.MARS: "♂",
    swe.JUPITER: "♃",
    swe.SATURN: "♄",
    swe.URANUS: "♅",
    swe.NEPTUNE: "♆",
    swe.PLUTO: "♇",
    swe.MEAN_NODE: "☊",
}

PLANETS = [
    swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS,
    swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO,
    swe.MEAN_NODE,
]

ASPECT_TYPES = {
    "Соединение": 0,
    "Секстиль": 60,
    "Квадрат": 90,
    "Тригон": 120,
    "Оппозиция": 180,
}

ASPECT_ORBS = {
    "Соединение": 8,
    "Секстиль": 6,
    "Квадрат": 7,
    "Тригон": 8,
    "Оппозиция": 8,
}


@dataclass
class PlanetPosition:
    planet_id: int
    name: str
    symbol: str
    longitude: float
    latitude: float
    sign: str
    sign_symbol: str
    sign_index: int
    degree_in_sign: float
    house: int = 0
    retrograde: bool = False


@dataclass
class Aspect:
    planet1: str
    planet2: str
    aspect_type: str
    angle: float
    orb: float
    exact_angle: float


@dataclass
class HouseData:
    number: int
    sign: str
    sign_symbol: str
    degree: float


@dataclass
class NatalChart:
    planets: list[PlanetPosition] = field(default_factory=list)
    houses: list[HouseData] = field(default_factory=list)
    aspects: list[Aspect] = field(default_factory=list)
    ascendant: float = 0.0
    midheaven: float = 0.0
    sun_sign: str = ""
    moon_sign: str = ""
    rising_sign: str = ""


def datetime_to_jd(dt: datetime) -> float:
    """Convert datetime to Julian Day number."""
    hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    return swe.julday(dt.year, dt.month, dt.day, hour)


def longitude_to_sign(longitude: float) -> tuple[str, str, int, float]:
    """Convert ecliptic longitude to zodiac sign info."""
    sign_index = int(longitude / 30)
    degree_in_sign = longitude % 30
    return (
        ZODIAC_SIGNS[sign_index],
        ZODIAC_SYMBOLS[sign_index],
        sign_index,
        degree_in_sign,
    )


def calculate_planet_positions(jd: float) -> list[PlanetPosition]:
    """Calculate positions of all planets for a given Julian Day."""
    positions = []
    for planet_id in PLANETS:
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        result, ret_flags = swe.calc_ut(jd, planet_id, flags)

        lon = result[0]
        lat = result[1]
        speed = result[3]

        sign, sign_sym, sign_idx, deg = longitude_to_sign(lon)

        positions.append(PlanetPosition(
            planet_id=planet_id,
            name=PLANET_NAMES[planet_id],
            symbol=PLANET_SYMBOLS[planet_id],
            longitude=lon,
            latitude=lat,
            sign=sign,
            sign_symbol=sign_sym,
            sign_index=sign_idx,
            degree_in_sign=deg,
            retrograde=speed < 0,
        ))

    return positions


def calculate_houses(jd: float, lat: float, lon: float) -> tuple[list[HouseData], float, float]:
    """Calculate house cusps using Placidus system."""
    cusps, ascmc = swe.houses(jd, lat, lon, b"P")

    houses = []
    for i in range(12):
        cusp_lon = cusps[i]
        sign, sign_sym, _, deg = longitude_to_sign(cusp_lon)
        houses.append(HouseData(
            number=i + 1,
            sign=sign,
            sign_symbol=sign_sym,
            degree=deg,
        ))

    ascendant = ascmc[0]
    midheaven = ascmc[1]
    return houses, ascendant, midheaven


def assign_planets_to_houses(
    planets: list[PlanetPosition], houses: list[HouseData], cusps_longitudes: list[float]
):
    """Assign each planet to its house based on cusp longitudes."""
    for planet in planets:
        planet.house = 1
        for i in range(12):
            next_i = (i + 1) % 12
            cusp = cusps_longitudes[i]
            next_cusp = cusps_longitudes[next_i]

            if next_cusp < cusp:  # wraps around 360
                if planet.longitude >= cusp or planet.longitude < next_cusp:
                    planet.house = i + 1
                    break
            else:
                if cusp <= planet.longitude < next_cusp:
                    planet.house = i + 1
                    break


def calculate_aspects(planets: list[PlanetPosition]) -> list[Aspect]:
    """Calculate major aspects between planets."""
    aspects = []
    for i in range(len(planets)):
        for j in range(i + 1, len(planets)):
            p1 = planets[i]
            p2 = planets[j]

            diff = abs(p1.longitude - p2.longitude)
            if diff > 180:
                diff = 360 - diff

            for aspect_name, exact_angle in ASPECT_TYPES.items():
                orb = abs(diff - exact_angle)
                if orb <= ASPECT_ORBS[aspect_name]:
                    aspects.append(Aspect(
                        planet1=p1.name,
                        planet2=p2.name,
                        aspect_type=aspect_name,
                        angle=diff,
                        orb=orb,
                        exact_angle=exact_angle,
                    ))

    return aspects


def calculate_natal_chart(
    birth_date: date,
    birth_time: time | None,
    latitude: float,
    longitude: float,
) -> NatalChart:
    """Calculate a complete natal chart."""
    bt = birth_time or time(12, 0)
    dt = datetime.combine(birth_date, bt)
    jd = datetime_to_jd(dt)

    planets = calculate_planet_positions(jd)

    cusps, ascmc = swe.houses(jd, latitude, longitude, b"P")
    cusps_list = list(cusps)

    houses = []
    for i in range(12):
        cusp_lon = cusps_list[i]
        sign, sign_sym, _, deg = longitude_to_sign(cusp_lon)
        houses.append(HouseData(
            number=i + 1,
            sign=sign,
            sign_symbol=sign_sym,
            degree=deg,
        ))

    ascendant = ascmc[0]
    midheaven = ascmc[1]

    assign_planets_to_houses(planets, houses, cusps_list)
    aspects = calculate_aspects(planets)

    sun_sign = ""
    moon_sign = ""
    for p in planets:
        if p.planet_id == swe.SUN:
            sun_sign = p.sign
        elif p.planet_id == swe.MOON:
            moon_sign = p.sign

    _, rising_sym, _, _ = longitude_to_sign(ascendant)
    rising_sign_name = ZODIAC_SIGNS[int(ascendant / 30)]

    return NatalChart(
        planets=planets,
        houses=houses,
        aspects=aspects,
        ascendant=ascendant,
        midheaven=midheaven,
        sun_sign=sun_sign,
        moon_sign=moon_sign,
        rising_sign=rising_sign_name,
    )


def get_current_transits() -> list[PlanetPosition]:
    """Get current planetary positions (transits)."""
    now = datetime.utcnow()
    jd = datetime_to_jd(now)
    return calculate_planet_positions(jd)


def calculate_transit_aspects(
    natal_planets: list[PlanetPosition],
    transit_planets: list[PlanetPosition],
    orb: float = 3.0,
) -> list[Aspect]:
    """Calculate aspects between transit and natal planets."""
    aspects = []
    for tp in transit_planets:
        for np_ in natal_planets:
            diff = abs(tp.longitude - np_.longitude)
            if diff > 180:
                diff = 360 - diff

            for aspect_name, exact_angle in ASPECT_TYPES.items():
                aspect_orb = abs(diff - exact_angle)
                if aspect_orb <= orb:
                    aspects.append(Aspect(
                        planet1=f"Транзит {tp.name}",
                        planet2=f"Натал {np_.name}",
                        aspect_type=aspect_name,
                        angle=diff,
                        orb=aspect_orb,
                        exact_angle=exact_angle,
                    ))

    return aspects


def format_chart_text(chart: NatalChart) -> str:
    """Format natal chart as readable text."""
    lines = ["🌟 Натальная карта\n"]
    lines.append(f"☀️ Солнце: {chart.sun_sign}")
    lines.append(f"🌙 Луна: {chart.moon_sign}")
    lines.append(f"⬆️ Асцендент: {chart.rising_sign}\n")

    lines.append("━━━ Планеты ━━━")
    for p in chart.planets:
        retro = " ℞" if p.retrograde else ""
        deg = int(p.degree_in_sign)
        mins = int((p.degree_in_sign - deg) * 60)
        lines.append(
            f"{p.symbol} {p.name}: {p.sign_symbol} {p.sign} {deg}°{mins:02d}'{retro} (дом {p.house})"
        )

    if chart.aspects:
        lines.append("\n━━━ Аспекты ━━━")
        for a in chart.aspects[:15]:
            lines.append(f"  {a.planet1} — {a.planet2}: {a.aspect_type} (орб {a.orb:.1f}°)")

    return "\n".join(lines)


def format_transits_text(
    natal_chart: NatalChart,
    transit_planets: list[PlanetPosition],
    transit_aspects: list[Aspect],
) -> str:
    """Format current transits as text."""
    lines = ["🔮 Текущие транзиты\n"]
    lines.append("━━━ Позиции планет ━━━")
    for p in transit_planets:
        retro = " ℞" if p.retrograde else ""
        deg = int(p.degree_in_sign)
        lines.append(f"{p.symbol} {p.name}: {p.sign_symbol} {p.sign} {deg}°{retro}")

    if transit_aspects:
        lines.append("\n━━━ Активные транзиты к натальной карте ━━━")
        for a in transit_aspects[:10]:
            lines.append(f"  {a.planet1} → {a.planet2}: {a.aspect_type} (орб {a.orb:.1f}°)")

    return "\n".join(lines)


def get_sun_sign(birth_date: date) -> str:
    """Get sun sign from birth date (simplified, no ephemeris needed)."""
    month, day = birth_date.month, birth_date.day
    signs = [
        ((1, 20), (2, 18), "Водолей"),
        ((2, 19), (3, 20), "Рыбы"),
        ((3, 21), (4, 19), "Овен"),
        ((4, 20), (5, 20), "Телец"),
        ((5, 21), (6, 20), "Близнецы"),
        ((6, 21), (7, 22), "Рак"),
        ((7, 23), (8, 22), "Лев"),
        ((8, 23), (9, 22), "Дева"),
        ((9, 23), (10, 22), "Весы"),
        ((10, 23), (11, 21), "Скорпион"),
        ((11, 22), (12, 21), "Стрелец"),
        ((12, 22), (1, 19), "Козерог"),
    ]
    for (sm, sd), (em, ed), sign in signs:
        if sm == 12 and em == 1:
            if (month == 12 and day >= sd) or (month == 1 and day <= ed):
                return sign
        elif (month == sm and day >= sd) or (month == em and day <= ed):
            return sign
    return "Козерог"
