from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time


@dataclass(frozen=True)
class BirthProfile:
    birth_date: date
    birth_time: time | None
    birth_place: str
    latitude: float | None = None
    longitude: float | None = None
    timezone: str | None = None


@dataclass(frozen=True)
class PlanetPosition:
    planet: str
    label: str
    longitude: float
    sign: str
    sign_index: int
    degree: float
    house: int | None = None


@dataclass(frozen=True)
class Aspect:
    planet_a: str
    planet_b: str
    aspect: str
    angle: int
    orb: float


@dataclass(frozen=True)
class Transit:
    transit_planet: str
    natal_planet: str
    aspect: str
    orb: float


@dataclass
class NatalChart:
    profile: BirthProfile
    calculated_for: datetime
    planets: list[PlanetPosition] = field(default_factory=list)
    aspects: list[Aspect] = field(default_factory=list)
    houses: list[float] = field(default_factory=list)
