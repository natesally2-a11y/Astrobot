"""Astrological calculations powered by Swiss Ephemeris.

The Swiss Ephemeris library ships with a built-in Moshier analytical
ephemeris that does not need the proprietary ``.se1`` data files, which keeps
the docker image lean.  We fall back to the bundled ephemeris if a dedicated
``EPHEMERIS_PATH`` is configured.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime, time, timezone
from typing import Optional
from zoneinfo import ZoneInfo

import swisseph as swe

from app.config import settings

# ----- Static astrological data -----

SIGNS_RU = [
    "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
    "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы",
]

SIGNS_EN = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

SIGN_GLYPH = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]

PLANETS: dict[str, int] = {
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
}

PLANET_GLYPHS = {
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

ASPECTS = {
    "Conjunction": (0, 8),
    "Opposition": (180, 8),
    "Trine": (120, 6),
    "Square": (90, 6),
    "Sextile": (60, 4),
}

ASPECT_NAMES_RU = {
    "Conjunction": "Соединение",
    "Opposition": "Оппозиция",
    "Trine": "Тригон",
    "Square": "Квадрат",
    "Sextile": "Секстиль",
}


# ----- Setup -----

_ephemeris_initialized = False


def _ensure_ephemeris() -> None:
    global _ephemeris_initialized
    if _ephemeris_initialized:
        return
    if settings.ephemeris_path:
        try:
            swe.set_ephe_path(settings.ephemeris_path)
        except Exception:
            pass
    _ephemeris_initialized = True


# ----- Data structures -----

@dataclass
class PlanetPosition:
    name: str
    longitude: float
    latitude: float
    distance: float
    speed: float
    retrograde: bool
    sign_index: int
    sign: str
    sign_glyph: str
    degree_in_sign: float
    house: Optional[int] = None

    def formatted(self, lang: str = "ru") -> str:
        ru_name = PLANET_NAMES_RU.get(self.name, self.name) if lang == "ru" else self.name
        deg = int(self.degree_in_sign)
        minutes = int(round((self.degree_in_sign - deg) * 60))
        retro = " R" if self.retrograde else ""
        return f"{PLANET_GLYPHS[self.name]} {ru_name}: {deg}°{minutes:02d}' {self.sign}{retro}"


@dataclass
class Aspect:
    body_a: str
    body_b: str
    aspect: str
    orb: float

    def formatted(self, lang: str = "ru") -> str:
        if lang == "ru":
            a = PLANET_NAMES_RU.get(self.body_a, self.body_a)
            b = PLANET_NAMES_RU.get(self.body_b, self.body_b)
            aspect_name = ASPECT_NAMES_RU.get(self.aspect, self.aspect)
        else:
            a, b, aspect_name = self.body_a, self.body_b, self.aspect
        return f"{a} {aspect_name} {b} (орб. {self.orb:.1f}°)"


@dataclass
class NatalChart:
    julian_day: float
    moment_utc: datetime
    latitude: float
    longitude: float
    timezone: str
    positions: dict[str, PlanetPosition]
    houses: list[float] = field(default_factory=list)
    ascendant: Optional[float] = None
    midheaven: Optional[float] = None
    aspects: list[Aspect] = field(default_factory=list)

    @property
    def has_houses(self) -> bool:
        return bool(self.houses)


# ----- Helpers -----

def sign_of(longitude: float) -> tuple[int, str, str, float]:
    longitude = longitude % 360
    idx = int(longitude // 30)
    deg = longitude - idx * 30
    return idx, SIGNS_RU[idx], SIGN_GLYPH[idx], deg


def _julian_day_utc(moment_utc: datetime) -> float:
    return swe.julday(
        moment_utc.year,
        moment_utc.month,
        moment_utc.day,
        moment_utc.hour + moment_utc.minute / 60 + moment_utc.second / 3600,
        swe.GREG_CAL,
    )


def _to_utc(birth_date: date, birth_time: Optional[time], tz_name: str) -> datetime:
    tz = ZoneInfo(tz_name) if tz_name else timezone.utc
    if birth_time is None:
        birth_time = time(12, 0)  # default to noon when time is unknown
    local_dt = datetime(
        birth_date.year,
        birth_date.month,
        birth_date.day,
        birth_time.hour,
        birth_time.minute,
        tzinfo=tz,
    )
    return local_dt.astimezone(timezone.utc)


def _planet_position(jd: float, planet_id: int, planet_name: str) -> PlanetPosition:
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    values, _ = swe.calc_ut(jd, planet_id, flags)
    longitude, latitude, distance, speed_long = values[0], values[1], values[2], values[3]
    idx, sign_name, sign_glyph, deg_in_sign = sign_of(longitude)
    return PlanetPosition(
        name=planet_name,
        longitude=longitude,
        latitude=latitude,
        distance=distance,
        speed=speed_long,
        retrograde=speed_long < 0,
        sign_index=idx,
        sign=sign_name,
        sign_glyph=sign_glyph,
        degree_in_sign=deg_in_sign,
    )


def _compute_houses(
    jd: float, lat: float, lon: float
) -> tuple[list[float], float, float]:
    try:
        cusps, ascmc = swe.houses(jd, lat, lon, b"P")
        return list(cusps), ascmc[0], ascmc[1]
    except Exception:
        return [], 0.0, 0.0


def _house_of(longitude: float, cusps: list[float]) -> Optional[int]:
    if not cusps:
        return None
    longitude = longitude % 360
    for i in range(12):
        start = cusps[i] % 360
        end = cusps[(i + 1) % 12] % 360
        if start <= end:
            if start <= longitude < end:
                return i + 1
        else:
            if longitude >= start or longitude < end:
                return i + 1
    return None


def _compute_aspects(positions: dict[str, PlanetPosition]) -> list[Aspect]:
    aspects: list[Aspect] = []
    names = list(positions.keys())
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            sep = abs(positions[a].longitude - positions[b].longitude) % 360
            if sep > 180:
                sep = 360 - sep
            for aspect_name, (angle, orb) in ASPECTS.items():
                diff = abs(sep - angle)
                if diff <= orb:
                    aspects.append(
                        Aspect(body_a=a, body_b=b, aspect=aspect_name, orb=diff)
                    )
                    break
    return aspects


# ----- Public API -----

def compute_natal_chart(
    *,
    birth_date: date,
    birth_time: Optional[time],
    latitude: Optional[float],
    longitude: Optional[float],
    tz_name: Optional[str],
) -> NatalChart:
    _ensure_ephemeris()

    lat = float(latitude) if latitude is not None else 0.0
    lon = float(longitude) if longitude is not None else 0.0
    tz = tz_name or "UTC"

    moment_utc = _to_utc(birth_date, birth_time, tz)
    jd = _julian_day_utc(moment_utc)

    positions = {
        name: _planet_position(jd, planet_id, name)
        for name, planet_id in PLANETS.items()
    }

    cusps, asc, mc = ([], None, None)
    if birth_time is not None and latitude is not None and longitude is not None:
        cusps, asc, mc = _compute_houses(jd, lat, lon)
        for pos in positions.values():
            pos.house = _house_of(pos.longitude, cusps)

    aspects = _compute_aspects(positions)

    return NatalChart(
        julian_day=jd,
        moment_utc=moment_utc,
        latitude=lat,
        longitude=lon,
        timezone=tz,
        positions=positions,
        houses=cusps,
        ascendant=asc,
        midheaven=mc,
        aspects=aspects,
    )


def compute_transits(
    chart: NatalChart, when_utc: Optional[datetime] = None
) -> list[Aspect]:
    """Return important transits between current planets and a natal chart."""
    _ensure_ephemeris()
    when_utc = when_utc or datetime.now(timezone.utc)
    jd = _julian_day_utc(when_utc)
    transit_positions = {
        name: _planet_position(jd, planet_id, name)
        for name, planet_id in PLANETS.items()
    }
    aspects: list[Aspect] = []
    for t_name, t_pos in transit_positions.items():
        for n_name, n_pos in chart.positions.items():
            sep = abs(t_pos.longitude - n_pos.longitude) % 360
            if sep > 180:
                sep = 360 - sep
            for aspect_name, (angle, orb) in ASPECTS.items():
                tight_orb = max(2.0, orb - 4)  # tighter for transits
                diff = abs(sep - angle)
                if diff <= tight_orb:
                    aspects.append(
                        Aspect(
                            body_a=f"t-{t_name}",
                            body_b=f"n-{n_name}",
                            aspect=aspect_name,
                            orb=diff,
                        )
                    )
                    break
    return aspects


def synastry(chart_a: NatalChart, chart_b: NatalChart) -> list[Aspect]:
    """Cross-aspects between two natal charts (compatibility)."""
    aspects: list[Aspect] = []
    for name_a, pos_a in chart_a.positions.items():
        for name_b, pos_b in chart_b.positions.items():
            sep = abs(pos_a.longitude - pos_b.longitude) % 360
            if sep > 180:
                sep = 360 - sep
            for aspect_name, (angle, orb) in ASPECTS.items():
                diff = abs(sep - angle)
                if diff <= orb:
                    aspects.append(
                        Aspect(
                            body_a=f"A-{name_a}",
                            body_b=f"B-{name_b}",
                            aspect=aspect_name,
                            orb=diff,
                        )
                    )
                    break
    return aspects


def summarize_chart(chart: NatalChart, lang: str = "ru") -> str:
    """A compact text dump used as a deterministic prompt for the LLM."""
    lines = []
    if chart.ascendant is not None:
        idx, sign, _, deg = sign_of(chart.ascendant)
        lines.append(f"Asc: {int(deg)}° {sign}")
    if chart.midheaven is not None:
        idx, sign, _, deg = sign_of(chart.midheaven)
        lines.append(f"MC: {int(deg)}° {sign}")
    for pos in chart.positions.values():
        line = pos.formatted(lang=lang)
        if pos.house:
            line += f" (дом {pos.house})" if lang == "ru" else f" (house {pos.house})"
        lines.append(line)
    if chart.aspects:
        lines.append("")
        lines.append("Аспекты:" if lang == "ru" else "Aspects:")
        for asp in chart.aspects[:15]:
            lines.append("  " + asp.formatted(lang=lang))
    return "\n".join(lines)


def degrees_to_dms(angle: float) -> str:
    deg = int(angle)
    minutes_full = (angle - deg) * 60
    minutes = int(minutes_full)
    seconds = int(round((minutes_full - minutes) * 60))
    return f"{deg}°{minutes:02d}'{seconds:02d}\""


def quick_sign_for(birth_date: date) -> str:
    """Crude Sun-sign helper for inline-mode shortcuts."""
    md = (birth_date.month, birth_date.day)
    cutoffs = [
        ((3, 21), "Овен"),
        ((4, 20), "Телец"),
        ((5, 21), "Близнецы"),
        ((6, 22), "Рак"),
        ((7, 23), "Лев"),
        ((8, 23), "Дева"),
        ((9, 23), "Весы"),
        ((10, 23), "Скорпион"),
        ((11, 22), "Стрелец"),
        ((12, 22), "Козерог"),
        ((1, 20), "Водолей"),
        ((2, 19), "Рыбы"),
    ]
    last = "Рыбы"
    for cutoff, sign in cutoffs:
        if md < cutoff:
            return last
        last = sign
    return "Овен"


def angle_between(a: float, b: float) -> float:
    diff = abs(a - b) % 360
    return diff if diff <= 180 else 360 - diff


def cycle_angle(angle: float) -> float:
    """Wrap an angle into [0, 360)."""
    return angle % 360


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))
