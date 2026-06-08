"""Astrological calculations powered by the Swiss Ephemeris (pyswisseph).

The Moshier ephemeris (built into pyswisseph) is used so the engine works out
of the box without downloading external ephemeris data files. Accuracy is more
than sufficient for natal interpretation.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import List, Optional

import swisseph as swe

from app.astrology.constants import (
    ASPECTS,
    PLANET_NAMES_RU,
    degree_to_sign,
)

# Use the Moshier ephemeris — no external .se1 files required.
_EPHE_FLAGS = swe.FLG_MOSEPH | swe.FLG_SPEED

# Swiss Ephemeris planet identifiers.
_PLANET_IDS = {
    "sun": swe.SUN,
    "moon": swe.MOON,
    "mercury": swe.MERCURY,
    "venus": swe.VENUS,
    "mars": swe.MARS,
    "jupiter": swe.JUPITER,
    "saturn": swe.SATURN,
    "uranus": swe.URANUS,
    "neptune": swe.NEPTUNE,
    "pluto": swe.PLUTO,
    "north_node": swe.TRUE_NODE,
    "chiron": swe.CHIRON,
}


@dataclass
class PlanetPosition:
    key: str
    name: str
    longitude: float          # absolute ecliptic longitude 0-360
    sign_index: int
    degree_in_sign: float
    speed: float              # degrees / day (negative => retrograde)
    house: Optional[int] = None

    @property
    def retrograde(self) -> bool:
        return self.speed < 0

    @property
    def position_str(self) -> str:
        from app.astrology.constants import SIGN_NAMES_RU

        d = int(self.degree_in_sign)
        m = int(round((self.degree_in_sign - d) * 60))
        if m == 60:
            d, m = d + 1, 0
        retro = " R" if self.retrograde else ""
        return f"{d}°{m:02d}′ {SIGN_NAMES_RU[self.sign_index]}{retro}"


@dataclass
class Aspect:
    body1: str
    body2: str
    name: str
    key: str
    angle: float
    orb: float

    @property
    def description(self) -> str:
        n1 = PLANET_NAMES_RU.get(self.body1, self.body1)
        n2 = PLANET_NAMES_RU.get(self.body2, self.body2)
        return f"{n1} {self.name.lower()} {n2} (орб {self.orb:.1f}°)"


@dataclass
class NatalChart:
    planets: List[PlanetPosition] = field(default_factory=list)
    aspects: List[Aspect] = field(default_factory=list)
    houses: List[float] = field(default_factory=list)  # 12 cusp longitudes
    ascendant: Optional[float] = None
    midheaven: Optional[float] = None
    has_houses: bool = False
    jd_ut: float = 0.0

    def planet(self, key: str) -> Optional[PlanetPosition]:
        for p in self.planets:
            if p.key == key:
                return p
        return None

    @property
    def sun_sign(self) -> Optional[int]:
        p = self.planet("sun")
        return p.sign_index if p else None

    @property
    def moon_sign(self) -> Optional[int]:
        p = self.planet("moon")
        return p.sign_index if p else None

    @property
    def ascendant_sign(self) -> Optional[int]:
        if self.ascendant is None:
            return None
        return degree_to_sign(self.ascendant)[0]


def to_julian_day(when_utc: dt.datetime) -> float:
    """Convert a timezone-aware (or naive-UTC) datetime to Julian Day (UT)."""
    if when_utc.tzinfo is not None:
        when_utc = when_utc.astimezone(dt.timezone.utc)
    hour = when_utc.hour + when_utc.minute / 60.0 + when_utc.second / 3600.0
    return swe.julday(when_utc.year, when_utc.month, when_utc.day, hour, swe.GREG_CAL)


def _house_of(longitude: float, cusps: List[float]) -> Optional[int]:
    """Determine which house a longitude falls into, given 12 cusps."""
    if not cusps or len(cusps) < 12:
        return None
    longitude = longitude % 360.0
    for i in range(12):
        start = cusps[i] % 360.0
        end = cusps[(i + 1) % 12] % 360.0
        if start <= end:
            if start <= longitude < end:
                return i + 1
        else:  # wrap across 360/0
            if longitude >= start or longitude < end:
                return i + 1
    return None


def compute_aspects(planets: List[PlanetPosition]) -> List[Aspect]:
    aspects: List[Aspect] = []
    for i in range(len(planets)):
        for j in range(i + 1, len(planets)):
            p1, p2 = planets[i], planets[j]
            diff = abs(p1.longitude - p2.longitude) % 360.0
            if diff > 180.0:
                diff = 360.0 - diff
            for name, key, angle, orb, _glyph in ASPECTS:
                delta = abs(diff - angle)
                if delta <= orb:
                    aspects.append(
                        Aspect(
                            body1=p1.key,
                            body2=p2.key,
                            name=name,
                            key=key,
                            angle=angle,
                            orb=round(delta, 2),
                        )
                    )
                    break
    # Tightest orbs first.
    aspects.sort(key=lambda a: a.orb)
    return aspects


def calculate_natal_chart(
    when_utc: dt.datetime,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    *,
    with_houses: bool = True,
) -> NatalChart:
    """Calculate a full natal chart.

    ``when_utc`` must already be in UTC. Houses/ascendant are computed only when
    coordinates are supplied and ``with_houses`` is True (i.e. birth time known).
    """
    jd = to_julian_day(when_utc)
    chart = NatalChart(jd_ut=jd)

    cusps: List[float] = []
    if with_houses and latitude is not None and longitude is not None:
        try:
            raw_cusps, ascmc = swe.houses(jd, float(latitude), float(longitude), b"P")
            cusps = list(raw_cusps[:12])
            chart.houses = cusps
            chart.ascendant = ascmc[0]
            chart.midheaven = ascmc[1]
            chart.has_houses = True
        except Exception:
            cusps = []

    for key, swe_id in _PLANET_IDS.items():
        try:
            result, _flag = swe.calc_ut(jd, swe_id, _EPHE_FLAGS)
        except Exception:
            continue
        lon = result[0] % 360.0
        speed = result[3]
        sign_idx, deg_in_sign = degree_to_sign(lon)
        pos = PlanetPosition(
            key=key,
            name=PLANET_NAMES_RU.get(key, key),
            longitude=lon,
            sign_index=sign_idx,
            degree_in_sign=deg_in_sign,
            speed=speed,
            house=_house_of(lon, cusps) if cusps else None,
        )
        chart.planets.append(pos)

    chart.aspects = compute_aspects(chart.planets)
    return chart


def calculate_transits(
    natal: NatalChart, when_utc: Optional[dt.datetime] = None
) -> List[Aspect]:
    """Aspects between current (transiting) planets and natal planets."""
    when_utc = when_utc or dt.datetime.now(dt.timezone.utc)
    jd = to_julian_day(when_utc)

    transit_positions: List[PlanetPosition] = []
    for key, swe_id in _PLANET_IDS.items():
        try:
            result, _flag = swe.calc_ut(jd, swe_id, _EPHE_FLAGS)
        except Exception:
            continue
        lon = result[0] % 360.0
        sign_idx, deg = degree_to_sign(lon)
        transit_positions.append(
            PlanetPosition(
                key=key,
                name=PLANET_NAMES_RU.get(key, key),
                longitude=lon,
                sign_index=sign_idx,
                degree_in_sign=deg,
                speed=result[3],
            )
        )

    transit_aspects: List[Aspect] = []
    for t in transit_positions:
        for n in natal.planets:
            diff = abs(t.longitude - n.longitude) % 360.0
            if diff > 180.0:
                diff = 360.0 - diff
            for name, akey, angle, orb, _glyph in ASPECTS:
                # Slightly tighter orb for transits.
                t_orb = min(orb, 5.0)
                if abs(diff - angle) <= t_orb:
                    transit_aspects.append(
                        Aspect(
                            body1=t.key,
                            body2=n.key,
                            name=name,
                            key=akey,
                            angle=angle,
                            orb=round(abs(diff - angle), 2),
                        )
                    )
                    break
    transit_aspects.sort(key=lambda a: a.orb)
    return transit_aspects
