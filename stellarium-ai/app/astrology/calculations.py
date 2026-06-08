"""
Astrological calculations using Swiss Ephemeris (pyswisseph).
Uses Moshier ephemeris (built-in, no data files required).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, date, time
from typing import Optional
import pytz

try:
    import swisseph as swe
    SWE_AVAILABLE = True
except ImportError:
    SWE_AVAILABLE = False

ZODIAC_SIGNS = [
    "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
    "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы",
]

ZODIAC_SIGNS_EN = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

ZODIAC_SYMBOLS = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]

PLANET_NAMES_RU = {
    "Sun": "Солнце",
    "Moon": "Луна",
    "Mercury": "Меркурий",
    "Venus": "Венера",
    "Mars": "Марс",
    "Jupiter": "Юпитер",
    "Saturn": "Сатурн",
    "Uranus": "Уран",
    "Neptune": "Нептун",
    "Pluto": "Плутон",
    "Ascendant": "Асцендент",
    "Midheaven": "МС (Середина Неба)",
}

PLANET_SYMBOLS = {
    "Sun": "☉",
    "Moon": "☽",
    "Mercury": "☿",
    "Venus": "♀",
    "Mars": "♂",
    "Jupiter": "♃",
    "Saturn": "♄",
    "Uranus": "♅",
    "Neptune": "♆",
    "Pluto": "♇",
}

if SWE_AVAILABLE:
    PLANET_IDS = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mercury": swe.MERCURY,
        "Venus": swe.VENUS,
        "Mars": swe.MARS,
        "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN,
        "Uranus": swe.URANUS,
        "Neptune": swe.NEPTUNE,
        "Pluto": swe.PLUTO,
    }
else:
    PLANET_IDS = {}

ASPECT_TYPES = {
    "Соединение": (0, 8, "conjunct"),
    "Оппозиция": (180, 8, "opposition"),
    "Тригон": (120, 8, "trine"),
    "Квадрат": (90, 7, "square"),
    "Секстиль": (60, 6, "sextile"),
    "Полусекстиль": (30, 2, "semisextile"),
    "Квинконс": (150, 3, "quincunx"),
}


@dataclass
class PlanetPosition:
    name: str
    longitude: float
    sign: str
    sign_ru: str
    sign_symbol: str
    degree: float
    minute: int
    sign_num: int
    retrograde: bool = False
    symbol: str = ""

    @property
    def formatted(self) -> str:
        retro = " ℞" if self.retrograde else ""
        return f"{self.symbol} {self.name}: {self.sign_symbol}{self.sign_ru} {int(self.degree)}°{self.minute:02d}'{retro}"


@dataclass
class Aspect:
    planet1: str
    planet2: str
    aspect_name: str
    angle: float
    orb: float
    is_applying: bool = False

    @property
    def formatted(self) -> str:
        return f"{PLANET_SYMBOLS.get(self.planet1, '')} {self.planet1} — {self.aspect_name} — {PLANET_SYMBOLS.get(self.planet2, '')} {self.planet2} (орб {self.orb:.1f}°)"


@dataclass
class NatalChart:
    birth_date: date
    birth_time: Optional[time]
    latitude: float
    longitude: float
    timezone: str
    planets: dict[str, PlanetPosition] = field(default_factory=dict)
    houses: list[float] = field(default_factory=list)
    ascendant: float = 0.0
    midheaven: float = 0.0
    aspects: list[Aspect] = field(default_factory=list)

    def __post_init__(self):
        self._calculate()

    def _calculate(self):
        if not SWE_AVAILABLE:
            self._calculate_fallback()
            return

        try:
            swe.set_ephe_path(None)
            jd = self._get_julian_day()

            flags = swe.FLG_MOSEPH

            for name, planet_id in PLANET_IDS.items():
                try:
                    result, _ = swe.calc_ut(jd, planet_id, flags)
                    longitude = result[0]
                    speed = result[3]
                    self.planets[name] = _make_planet_position(name, longitude, speed < 0)
                except Exception:
                    pass

            try:
                cusps, ascmc = swe.houses(jd, self.latitude, self.longitude, b"P")
                self.houses = list(cusps)
                self.ascendant = ascmc[0]
                self.midheaven = ascmc[1]
                self.planets["Ascendant"] = _make_planet_position("Ascendant", self.ascendant)
            except Exception:
                pass

            self.aspects = _calculate_aspects(self.planets)

        except Exception:
            self._calculate_fallback()

    def _get_julian_day(self) -> float:
        tz = pytz.timezone(self.timezone)
        if self.birth_time:
            local_dt = tz.localize(
                datetime.combine(self.birth_date, self.birth_time)
            )
        else:
            local_dt = tz.localize(
                datetime.combine(self.birth_date, time(12, 0))
            )
        utc_dt = local_dt.astimezone(pytz.utc)
        hour = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
        return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour)

    def _calculate_fallback(self):
        """Simple fallback Sun sign calculation when swisseph is unavailable."""
        doy = (self.birth_date - date(self.birth_date.year, 1, 1)).days
        sun_longitude = (doy / 365.25) * 360.0
        self.planets["Sun"] = _make_planet_position("Sun", sun_longitude % 360)

    def get_sun_sign(self) -> str:
        if "Sun" in self.planets:
            return self.planets["Sun"].sign_ru
        return "Неизвестно"

    def get_moon_sign(self) -> str:
        if "Moon" in self.planets:
            return self.planets["Moon"].sign_ru
        return "Неизвестно"

    def get_ascendant_sign(self) -> str:
        if "Ascendant" in self.planets:
            return self.planets["Ascendant"].sign_ru
        return "Неизвестно"

    def to_dict(self) -> dict:
        return {
            "birth_date": self.birth_date.isoformat(),
            "birth_time": self.birth_time.isoformat() if self.birth_time else None,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timezone": self.timezone,
            "planets": {
                name: {
                    "longitude": p.longitude,
                    "sign": p.sign,
                    "sign_ru": p.sign_ru,
                    "degree": p.degree,
                    "minute": p.minute,
                    "retrograde": p.retrograde,
                }
                for name, p in self.planets.items()
            },
            "houses": self.houses,
            "ascendant": self.ascendant,
            "midheaven": self.midheaven,
            "aspects": [
                {
                    "planet1": a.planet1,
                    "planet2": a.planet2,
                    "aspect_name": a.aspect_name,
                    "angle": a.angle,
                    "orb": a.orb,
                }
                for a in self.aspects
            ],
        }


def _make_planet_position(name: str, longitude: float, retrograde: bool = False) -> PlanetPosition:
    longitude = longitude % 360
    sign_num = int(longitude / 30)
    degree = longitude % 30
    minute = int((degree - int(degree)) * 60)
    return PlanetPosition(
        name=name,
        longitude=longitude,
        sign=ZODIAC_SIGNS_EN[sign_num],
        sign_ru=ZODIAC_SIGNS[sign_num],
        sign_symbol=ZODIAC_SYMBOLS[sign_num],
        degree=degree,
        minute=minute,
        sign_num=sign_num,
        retrograde=retrograde,
        symbol=PLANET_SYMBOLS.get(name, ""),
    )


def _calculate_aspects(planets: dict[str, PlanetPosition]) -> list[Aspect]:
    aspects = []
    planet_names = [k for k in planets if k != "Ascendant"]

    for i, p1 in enumerate(planet_names):
        for p2 in planet_names[i + 1:]:
            lon1 = planets[p1].longitude
            lon2 = planets[p2].longitude
            diff = abs(lon1 - lon2)
            if diff > 180:
                diff = 360 - diff

            for aspect_name, (angle, max_orb, _) in ASPECT_TYPES.items():
                orb = abs(diff - angle)
                if orb <= max_orb:
                    aspects.append(Aspect(
                        planet1=p1,
                        planet2=p2,
                        aspect_name=aspect_name,
                        angle=angle,
                        orb=orb,
                    ))
    return aspects


def get_current_transits(chart: NatalChart) -> NatalChart:
    """Get current planetary positions (transits) relative to natal chart."""
    now = datetime.utcnow()
    transit_chart = NatalChart(
        birth_date=now.date(),
        birth_time=now.time(),
        latitude=chart.latitude,
        longitude=chart.longitude,
        timezone="UTC",
    )
    return transit_chart


def get_aspects(chart: NatalChart) -> list[Aspect]:
    return chart.aspects


def degrees_to_dms(degrees: float) -> str:
    d = int(degrees)
    m = int((degrees - d) * 60)
    return f"{d}°{m:02d}'"


def get_sun_sign_from_date(birth_date: date) -> str:
    """Quick sun sign calculation without full chart."""
    m, d = birth_date.month, birth_date.day
    sun_sign_dates = [
        (3, 21, "Овен"), (4, 20, "Телец"), (5, 21, "Близнецы"),
        (6, 21, "Рак"), (7, 23, "Лев"), (8, 23, "Дева"),
        (9, 23, "Весы"), (10, 23, "Скорпион"), (11, 22, "Стрелец"),
        (12, 22, "Козерог"), (1, 20, "Водолей"), (2, 19, "Рыбы"),
    ]
    for i, (sm, sd, sign) in enumerate(sun_sign_dates):
        next_m, next_d, _ = sun_sign_dates[(i + 1) % 12]
        if (m == sm and d >= sd) or (m == next_m and d < next_d):
            return sign
    return "Козерог"
