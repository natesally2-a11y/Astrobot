from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

try:
    import swisseph as swe
except ImportError:  # pragma: no cover - optional dependency at runtime
    swe = None


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

PLANET_CODES = {
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

ASPECTS = {
    "conjunction": 0,
    "opposition": 180,
    "trine": 120,
    "square": 90,
    "sextile": 60,
}


@dataclass(slots=True)
class PlanetPlacement:
    name: str
    longitude: float
    sign: str
    degree_in_sign: float
    house: int


@dataclass(slots=True)
class Aspect:
    planet_a: str
    planet_b: str
    aspect_type: str
    orb: float


@dataclass(slots=True)
class ChartData:
    birth_date: str
    birth_time: str | None
    birth_place: str
    latitude: float
    longitude: float
    timezone: str
    planets: list[PlanetPlacement]
    aspects: list[Aspect]
    summary: str

    def as_dict(self) -> dict:
        return {
            "birth_date": self.birth_date,
            "birth_time": self.birth_time,
            "birth_place": self.birth_place,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timezone": self.timezone,
            "planets": [asdict(item) for item in self.planets],
            "aspects": [asdict(item) for item in self.aspects],
            "summary": self.summary,
        }


def _resolve_datetime(
    birth_date: date,
    birth_time: time | None,
    timezone_name: str,
) -> datetime:
    local_dt = datetime.combine(birth_date, birth_time or time(hour=12, minute=0))
    tz = ZoneInfo(timezone_name)
    return local_dt.replace(tzinfo=tz).astimezone(UTC)


def _longitude_to_sign(longitude: float) -> tuple[str, float]:
    normalized = longitude % 360
    sign_index = int(normalized // 30)
    return SIGNS[sign_index], normalized % 30


def _estimate_house(longitude: float, ascendant_longitude: float) -> int:
    relative = (longitude - ascendant_longitude) % 360
    return int(relative // 30) + 1


def _fallback_longitude(seed: float, multiplier: float) -> float:
    return (seed * multiplier) % 360


def _calculate_planet_longitudes(timestamp_utc: datetime) -> dict[str, float]:
    if swe is None:
        seed = timestamp_utc.toordinal() + (timestamp_utc.hour / 24) + (timestamp_utc.minute / 1440)
        multipliers = {
            "Sun": 0.9856,
            "Moon": 13.1764,
            "Mercury": 1.3833,
            "Venus": 1.2,
            "Mars": 0.524,
            "Jupiter": 0.083,
            "Saturn": 0.033,
            "Uranus": 0.012,
            "Neptune": 0.006,
            "Pluto": 0.004,
        }
        return {
            name: _fallback_longitude(seed, multiplier)
            for name, multiplier in multipliers.items()
        }

    julian_day = swe.julday(
        timestamp_utc.year,
        timestamp_utc.month,
        timestamp_utc.day,
        timestamp_utc.hour + (timestamp_utc.minute / 60),
    )
    values: dict[str, float] = {}
    for name, code in PLANET_CODES.items():
        position, _ = swe.calc_ut(julian_day, code)
        values[name] = float(position[0])
    return values


def _calculate_ascendant_longitude(
    timestamp_utc: datetime,
    latitude: float,
    longitude: float,
) -> float:
    if swe is None:
        return (longitude + timestamp_utc.hour * 15) % 360

    julian_day = swe.julday(
        timestamp_utc.year,
        timestamp_utc.month,
        timestamp_utc.day,
        timestamp_utc.hour + (timestamp_utc.minute / 60),
    )
    cusps, ascmc = swe.houses(julian_day, latitude, longitude)
    return float(ascmc[0])


def _build_aspects(planets: list[PlanetPlacement], orb_limit: float = 6.0) -> list[Aspect]:
    aspects: list[Aspect] = []
    for index, planet_a in enumerate(planets):
        for planet_b in planets[index + 1 :]:
            delta = abs(planet_a.longitude - planet_b.longitude)
            delta = min(delta, 360 - delta)
            for aspect_type, angle in ASPECTS.items():
                orb = abs(delta - angle)
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


def build_chart_summary(planets: list[PlanetPlacement], aspects: list[Aspect]) -> str:
    core = ", ".join(
        f"{planet.name} in {planet.sign} (house {planet.house})"
        for planet in planets[:5]
    )
    aspect_text = ", ".join(
        f"{aspect.planet_a}-{aspect.planet_b} {aspect.aspect_type}"
        for aspect in aspects[:5]
    ) or "few major aspects"
    return f"Core placements: {core}. Dominant patterns: {aspect_text}."


def calculate_natal_chart(
    birth_date: date,
    birth_time: time | None,
    birth_place: str,
    latitude: float,
    longitude: float,
    timezone_name: str,
) -> ChartData:
    timestamp_utc = _resolve_datetime(birth_date, birth_time, timezone_name)
    longitudes = _calculate_planet_longitudes(timestamp_utc)
    ascendant_longitude = _calculate_ascendant_longitude(timestamp_utc, latitude, longitude)

    planets: list[PlanetPlacement] = []
    for name, planet_longitude in longitudes.items():
        sign, degree_in_sign = _longitude_to_sign(planet_longitude)
        planets.append(
            PlanetPlacement(
                name=name,
                longitude=round(planet_longitude, 3),
                sign=sign,
                degree_in_sign=round(degree_in_sign, 3),
                house=_estimate_house(planet_longitude, ascendant_longitude),
            )
        )

    planets.sort(key=lambda item: item.longitude)
    aspects = _build_aspects(planets)
    summary = build_chart_summary(planets, aspects)
    return ChartData(
        birth_date=birth_date.isoformat(),
        birth_time=birth_time.strftime("%H:%M") if birth_time else None,
        birth_place=birth_place,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone_name,
        planets=planets,
        aspects=aspects,
        summary=summary,
    )


def calculate_transits(chart: ChartData, reference_dt: datetime | None = None) -> list[dict[str, str | float]]:
    reference_dt = reference_dt or datetime.now(UTC)
    transit_longitudes = _calculate_planet_longitudes(reference_dt)
    results: list[dict[str, str | float]] = []
    for natal_planet in chart.planets:
        for transit_name, transit_longitude in transit_longitudes.items():
            delta = abs(natal_planet.longitude - transit_longitude)
            delta = min(delta, 360 - delta)
            for aspect_type, angle in ASPECTS.items():
                orb = abs(delta - angle)
                if orb <= 3:
                    results.append(
                        {
                            "transit_planet": transit_name,
                            "natal_planet": natal_planet.name,
                            "aspect": aspect_type,
                            "orb": round(orb, 2),
                        }
                    )
                    break
    return results[:10]


def compatibility_score(first_chart: ChartData, second_chart: ChartData) -> dict[str, object]:
    shared_aspects = 0
    harmony_points = 0.0
    for first_planet in first_chart.planets:
        for second_planet in second_chart.planets:
            delta = abs(first_planet.longitude - second_planet.longitude)
            delta = min(delta, 360 - delta)
            if abs(delta - 120) <= 6 or abs(delta - 60) <= 4:
                shared_aspects += 1
                harmony_points += 1.2
            elif abs(delta - 180) <= 6 or abs(delta - 90) <= 5:
                shared_aspects += 1
                harmony_points += 0.7
            elif abs(delta) <= 6:
                shared_aspects += 1
                harmony_points += 1.0

    score = min(100, int(45 + harmony_points * 2.5))
    return {
        "score": score,
        "shared_aspects": shared_aspects,
        "summary": (
            f"Compatibility score {score}/100 with {shared_aspects} notable synastry links."
        ),
    }


def sign_forecast(sign: str, period: str) -> str:
    normalized = sign.capitalize()
    sign_seed = SIGNS.index(normalized) if normalized in SIGNS else 0
    themes = [
        "relationships",
        "focus",
        "money",
        "rest",
        "communication",
        "career",
        "intuition",
    ]
    advice = [
        "trust your first instinct",
        "move slowly and double-check details",
        "leave margin for spontaneous opportunities",
        "set one clear priority",
        "protect your energy from distractions",
    ]
    theme = themes[(sign_seed + len(period)) % len(themes)]
    tip = advice[(sign_seed * 3 + len(period)) % len(advice)]
    return (
        f"For {normalized}, the {period} spotlight falls on {theme}. "
        f"Use the window to {tip}."
    )


def polar_to_cartesian(longitude: float, radius: float, center_x: float, center_y: float) -> tuple[float, float]:
    angle = math.radians(longitude - 90)
    return (
        round(center_x + radius * math.cos(angle), 2),
        round(center_y + radius * math.sin(angle), 2),
    )
