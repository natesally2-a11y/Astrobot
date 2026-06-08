"""Астрологические расчёты на базе Swiss Ephemeris (pyswisseph).

Используется встроенная эфемерида Moshier (FLG_MOSEPH), поэтому внешние
файлы эфемерид не требуются — удобно для быстрого деплоя MVP.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

import swisseph as swe

from app.astrology.constants import (
    ASPECTS,
    PLANETS,
    degree_in_sign,
    element_of_sign,
    sign_index,
    sign_name,
)

# Базовый набор флагов: гелиоцентрическая -> геоцентрическая эклиптика,
# скорость планет, эфемерида Moshier (без файлов данных).
_FLAGS = swe.FLG_MOSEPH | swe.FLG_SPEED

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
    "north_node": swe.MEAN_NODE,
}


@dataclass
class PlanetPosition:
    key: str
    name: str
    symbol: str
    longitude: float
    sign_index: int
    sign: str
    degree: float
    retrograde: bool
    house: int | None = None

    @property
    def element(self) -> str:
        return element_of_sign(self.sign_index)


@dataclass
class Aspect:
    body1: str
    body2: str
    name: str
    symbol: str
    angle: float
    orb: float


@dataclass
class NatalChart:
    julian_day: float
    utc_datetime: dt.datetime
    latitude: float
    longitude: float
    has_time: bool
    planets: list[PlanetPosition] = field(default_factory=list)
    houses: list[float] = field(default_factory=list)  # куспиды 12 домов
    ascendant: float | None = None
    midheaven: float | None = None
    aspects: list[Aspect] = field(default_factory=list)

    def planet(self, key: str) -> PlanetPosition | None:
        for p in self.planets:
            if p.key == key:
                return p
        return None


def to_julian_day(utc: dt.datetime) -> float:
    hour = utc.hour + utc.minute / 60 + utc.second / 3600
    return swe.julday(utc.year, utc.month, utc.day, hour, swe.GREG_CAL)


def _house_of(longitude: float, cusps: list[float]) -> int | None:
    if not cusps or len(cusps) < 12:
        return None
    lon = longitude % 360
    for i in range(12):
        start = cusps[i] % 360
        end = cusps[(i + 1) % 12] % 360
        if start <= end:
            if start <= lon < end:
                return i + 1
        else:  # дом пересекает 0°
            if lon >= start or lon < end:
                return i + 1
    return None


def compute_chart(
    utc_datetime: dt.datetime,
    latitude: float,
    longitude: float,
    has_time: bool = True,
) -> NatalChart:
    """Рассчитать натальную карту по моменту в UTC и координатам."""
    jd = to_julian_day(utc_datetime)

    chart = NatalChart(
        julian_day=jd,
        utc_datetime=utc_datetime,
        latitude=latitude,
        longitude=longitude,
        has_time=has_time,
    )

    # Дома и угловые точки рассчитываются только при известном времени.
    cusps: list[float] = []
    if has_time:
        try:
            cusps_raw, ascmc = swe.houses(jd, latitude, longitude, b"P")
            cusps = list(cusps_raw)
            chart.houses = cusps
            chart.ascendant = ascmc[0]
            chart.midheaven = ascmc[1]
        except Exception:
            cusps = []

    for key, body_id in _PLANET_IDS.items():
        try:
            values, _ = swe.calc_ut(jd, body_id, _FLAGS)
        except Exception:
            continue
        lon = values[0] % 360
        speed = values[3]
        idx = sign_index(lon)
        name, symbol = PLANETS[key]
        pos = PlanetPosition(
            key=key,
            name=name,
            symbol=symbol,
            longitude=lon,
            sign_index=idx,
            sign=sign_name(lon),
            degree=degree_in_sign(lon),
            retrograde=speed < 0,
            house=_house_of(lon, cusps) if cusps else None,
        )
        chart.planets.append(pos)

    chart.aspects = compute_aspects(chart.planets)
    return chart


def compute_aspects(planets: list[PlanetPosition]) -> list[Aspect]:
    aspects: list[Aspect] = []
    for i in range(len(planets)):
        for j in range(i + 1, len(planets)):
            p1, p2 = planets[i], planets[j]
            diff = abs(p1.longitude - p2.longitude) % 360
            if diff > 180:
                diff = 360 - diff
            for name, (angle, orb, symbol) in ASPECTS.items():
                delta = abs(diff - angle)
                if delta <= orb:
                    aspects.append(
                        Aspect(
                            body1=p1.key,
                            body2=p2.key,
                            name=name,
                            symbol=symbol,
                            angle=angle,
                            orb=round(delta, 2),
                        )
                    )
                    break
    return aspects


def compute_transits(
    natal: NatalChart, when_utc: dt.datetime | None = None
) -> list[Aspect]:
    """Транзитные аспекты текущих планет к натальным позициям."""
    when_utc = when_utc or dt.datetime.now(dt.timezone.utc)
    jd = to_julian_day(when_utc)

    transit_positions: list[PlanetPosition] = []
    for key, body_id in _PLANET_IDS.items():
        try:
            values, _ = swe.calc_ut(jd, body_id, _FLAGS)
        except Exception:
            continue
        lon = values[0] % 360
        name, symbol = PLANETS[key]
        transit_positions.append(
            PlanetPosition(
                key=key,
                name=name,
                symbol=symbol,
                longitude=lon,
                sign_index=sign_index(lon),
                sign=sign_name(lon),
                degree=degree_in_sign(lon),
                retrograde=values[3] < 0,
            )
        )

    result: list[Aspect] = []
    # Для транзитов используем более узкие орбисы.
    transit_aspects = {
        "Соединение": (0, 3, "☌"),
        "Оппозиция": (180, 3, "☍"),
        "Тригон": (120, 3, "△"),
        "Квадрат": (90, 3, "□"),
        "Секстиль": (60, 2, "✶"),
    }
    for tp in transit_positions:
        for np in natal.planets:
            diff = abs(tp.longitude - np.longitude) % 360
            if diff > 180:
                diff = 360 - diff
            for name, (angle, orb, symbol) in transit_aspects.items():
                delta = abs(diff - angle)
                if delta <= orb:
                    result.append(
                        Aspect(
                            body1=f"транзитный {tp.name}",
                            body2=f"натальный {np.name}",
                            name=name,
                            symbol=symbol,
                            angle=angle,
                            orb=round(delta, 2),
                        )
                    )
                    break
    return result


def sign_for_date(date: dt.date) -> str:
    """Солнечный знак для приблизительных запросов (inline-режим)."""
    utc = dt.datetime(date.year, date.month, date.day, 12, 0, tzinfo=dt.timezone.utc)
    jd = to_julian_day(utc)
    values, _ = swe.calc_ut(jd, swe.SUN, _FLAGS)
    return sign_name(values[0])
