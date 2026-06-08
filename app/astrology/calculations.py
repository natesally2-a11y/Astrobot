"""Swiss-Ephemeris based astrological calculations.

We expose a small dataclass-based API: ``compute_chart`` returns a
:class:`NatalChart` containing planet positions, houses, the ascendant,
midheaven and a basic aspect list.  All angles are degrees in the tropical
zodiac (0..360).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, List, Optional, Tuple

try:
    import swisseph as swe  # type: ignore
    SWE_AVAILABLE = True
except Exception:  # pragma: no cover — optional at import time
    swe = None  # type: ignore
    SWE_AVAILABLE = False

import pytz
from timezonefinder import TimezoneFinder

from app.config import get_settings


# --- Constants -------------------------------------------------------------

ZODIAC_SIGNS = [
    ("Aries", "Овен", "♈"),
    ("Taurus", "Телец", "♉"),
    ("Gemini", "Близнецы", "♊"),
    ("Cancer", "Рак", "♋"),
    ("Leo", "Лев", "♌"),
    ("Virgo", "Дева", "♍"),
    ("Libra", "Весы", "♎"),
    ("Scorpio", "Скорпион", "♏"),
    ("Sagittarius", "Стрелец", "♐"),
    ("Capricorn", "Козерог", "♑"),
    ("Aquarius", "Водолей", "♒"),
    ("Pisces", "Рыбы", "♓"),
]

PLANETS: Dict[str, Tuple[Optional[int], str, str]] = {
    # name -> (swe constant, russian name, glyph)
    "Sun":     (0, "Солнце", "☉"),
    "Moon":    (1, "Луна", "☽"),
    "Mercury": (2, "Меркурий", "☿"),
    "Venus":   (3, "Венера", "♀"),
    "Mars":    (4, "Марс", "♂"),
    "Jupiter": (5, "Юпитер", "♃"),
    "Saturn":  (6, "Сатурн", "♄"),
    "Uranus":  (7, "Уран", "♅"),
    "Neptune": (8, "Нептун", "♆"),
    "Pluto":   (9, "Плутон", "♇"),
}

MAJOR_ASPECTS: List[Tuple[str, str, float, float]] = [
    # (name_en, name_ru, angle, orb)
    ("conjunction", "соединение", 0.0, 8.0),
    ("opposition",  "оппозиция",  180.0, 8.0),
    ("trine",       "тригон",     120.0, 7.0),
    ("square",      "квадрат",    90.0, 7.0),
    ("sextile",     "секстиль",   60.0, 5.0),
]


_TF: Optional[TimezoneFinder] = None
_SWE_INITIALIZED = False


def _ensure_swe_initialized() -> None:
    """Configure Swiss Ephemeris with optional ephemeris files path."""
    global _SWE_INITIALIZED
    if _SWE_INITIALIZED or not SWE_AVAILABLE:
        return
    settings = get_settings()
    if settings.swe_ephe_path:
        try:
            swe.set_ephe_path(settings.swe_ephe_path)
        except Exception:
            pass
    _SWE_INITIALIZED = True


def _tf() -> TimezoneFinder:
    global _TF
    if _TF is None:
        _TF = TimezoneFinder()
    return _TF


# --- Data structures -------------------------------------------------------

@dataclass
class PlanetPosition:
    name: str
    name_ru: str
    glyph: str
    longitude: float          # absolute ecliptic longitude (0..360)
    sign_index: int           # 0..11
    sign_degree: float        # 0..30
    house: Optional[int] = None
    retrograde: bool = False

    @property
    def sign_en(self) -> str:
        return ZODIAC_SIGNS[self.sign_index][0]

    @property
    def sign_ru(self) -> str:
        return ZODIAC_SIGNS[self.sign_index][1]

    @property
    def sign_glyph(self) -> str:
        return ZODIAC_SIGNS[self.sign_index][2]


@dataclass
class Aspect:
    planet_a: str
    planet_b: str
    name: str
    name_ru: str
    angle: float
    orb: float
    exact_angle: float


@dataclass
class NatalChart:
    julian_day: float
    latitude: float
    longitude: float
    timezone: Optional[str]
    planets: Dict[str, PlanetPosition] = field(default_factory=dict)
    houses: List[float] = field(default_factory=list)
    ascendant: Optional[float] = None
    midheaven: Optional[float] = None
    aspects: List[Aspect] = field(default_factory=list)
    time_is_unknown: bool = False

    def sun_sign_ru(self) -> str:
        sun = self.planets.get("Sun")
        return sun.sign_ru if sun else "—"

    def moon_sign_ru(self) -> str:
        moon = self.planets.get("Moon")
        return moon.sign_ru if moon else "—"

    def ascendant_sign_ru(self) -> str:
        if self.ascendant is None:
            return "—"
        return ZODIAC_SIGNS[int(self.ascendant // 30)][1]


# --- Geo helpers -----------------------------------------------------------

def timezone_for(latitude: float, longitude: float) -> str:
    tz = _tf().timezone_at(lat=latitude, lng=longitude)
    return tz or "UTC"


def to_julian_day_ut(
    birth_date: date,
    birth_time: Optional[time],
    latitude: float,
    longitude: float,
    timezone_name: Optional[str] = None,
) -> Tuple[float, str]:
    """Convert a local birth datetime into a Julian Day (UT) and resolved TZ."""
    if timezone_name is None:
        timezone_name = timezone_for(latitude, longitude)
    tz = pytz.timezone(timezone_name)
    bt = birth_time or time(12, 0)
    local_dt = tz.localize(datetime.combine(birth_date, bt))
    utc_dt = local_dt.astimezone(pytz.UTC)

    if SWE_AVAILABLE:
        ut_hours = utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600
        jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, ut_hours)
        return jd, timezone_name

    # Fallback Julian Day calculation (good to ~1s) if Swiss Ephemeris missing.
    epoch = datetime(2000, 1, 1, 12, tzinfo=pytz.UTC)
    delta = utc_dt - epoch
    jd = 2451545.0 + delta.total_seconds() / 86400.0
    return jd, timezone_name


# --- Fallback (Moshier-free) approximation --------------------------------

def _approx_mean_longitude(jd: float, planet: str) -> float:
    """Very rough mean longitude approximation when Swiss Ephemeris is absent.

    This is *only* used in environments where ``pyswisseph`` cannot be
    installed (e.g. CI sandboxes); accuracy is on the order of degrees but it
    keeps the bot operational and the tests deterministic.
    """
    # T = Julian centuries since J2000.0
    T = (jd - 2451545.0) / 36525.0
    base = {
        "Sun":     (280.4665, 36000.7698),
        "Moon":    (218.3164, 481267.8813),
        "Mercury": (252.2509, 149472.6746),
        "Venus":   (181.9798, 58517.8156),
        "Mars":    (355.4330, 19140.2993),
        "Jupiter": (34.3515, 3034.9057),
        "Saturn":  (50.0775, 1222.1138),
        "Uranus":  (314.0550, 428.4669),
        "Neptune": (304.3487, 218.4862),
        "Pluto":   (238.9290, 145.2078),
    }[planet]
    lon = (base[0] + base[1] * T) % 360
    return lon


# --- Public API ------------------------------------------------------------

def compute_chart(
    birth_date: date,
    birth_time: Optional[time],
    latitude: float,
    longitude: float,
    timezone_name: Optional[str] = None,
) -> NatalChart:
    """Compute a natal chart for the given birth data."""
    _ensure_swe_initialized()
    time_is_unknown = birth_time is None

    jd, tz_name = to_julian_day_ut(
        birth_date, birth_time, latitude, longitude, timezone_name
    )

    chart = NatalChart(
        julian_day=jd,
        latitude=latitude,
        longitude=longitude,
        timezone=tz_name,
        time_is_unknown=time_is_unknown,
    )

    # --- Planets ---
    if SWE_AVAILABLE:
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        try:
            swe.calc_ut(jd, swe.SUN, flags)
        except Exception:
            # Fall back to Moshier model (no ephemeris files required).
            flags = swe.FLG_MOSEPH | swe.FLG_SPEED

        for name, (code, name_ru, glyph) in PLANETS.items():
            try:
                xx, _ret = swe.calc_ut(jd, code, flags)
                lon = float(xx[0]) % 360
                speed = float(xx[3]) if len(xx) > 3 else 0.0
                retrograde = speed < 0
            except Exception:
                lon = _approx_mean_longitude(jd, name)
                retrograde = False
            chart.planets[name] = PlanetPosition(
                name=name,
                name_ru=name_ru,
                glyph=glyph,
                longitude=lon,
                sign_index=int(lon // 30),
                sign_degree=lon % 30,
                retrograde=retrograde,
            )
    else:
        for name, (_code, name_ru, glyph) in PLANETS.items():
            lon = _approx_mean_longitude(jd, name)
            chart.planets[name] = PlanetPosition(
                name=name,
                name_ru=name_ru,
                glyph=glyph,
                longitude=lon,
                sign_index=int(lon // 30),
                sign_degree=lon % 30,
                retrograde=False,
            )

    # --- Houses / angles ---
    if SWE_AVAILABLE and not time_is_unknown:
        try:
            cusps, ascmc = swe.houses(jd, latitude, longitude, b"P")
            chart.houses = [float(c) % 360 for c in cusps[:12]]
            chart.ascendant = float(ascmc[0]) % 360
            chart.midheaven = float(ascmc[1]) % 360
            _assign_houses(chart)
        except Exception:
            pass

    # --- Aspects ---
    chart.aspects = _compute_aspects(chart)
    return chart


def _assign_houses(chart: NatalChart) -> None:
    """Determine which house each planet falls into (Placidus cusps)."""
    if not chart.houses:
        return
    for planet in chart.planets.values():
        lon = planet.longitude
        for i in range(12):
            start = chart.houses[i]
            end = chart.houses[(i + 1) % 12]
            if start < end:
                if start <= lon < end:
                    planet.house = i + 1
                    break
            else:  # wraps over 360°
                if lon >= start or lon < end:
                    planet.house = i + 1
                    break


def _compute_aspects(chart: NatalChart) -> List[Aspect]:
    names = list(chart.planets.keys())
    out: List[Aspect] = []
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            la = chart.planets[a].longitude
            lb = chart.planets[b].longitude
            diff = abs(la - lb) % 360
            if diff > 180:
                diff = 360 - diff
            for asp_en, asp_ru, angle, orb in MAJOR_ASPECTS:
                delta = abs(diff - angle)
                if delta <= orb:
                    out.append(
                        Aspect(
                            planet_a=a,
                            planet_b=b,
                            name=asp_en,
                            name_ru=asp_ru,
                            angle=angle,
                            orb=delta,
                            exact_angle=diff,
                        )
                    )
                    break
    return out


def compute_transits(target_date: Optional[date] = None) -> Dict[str, PlanetPosition]:
    """Compute today's planet positions (used for prognosis)."""
    target_date = target_date or date.today()
    chart = compute_chart(
        birth_date=target_date,
        birth_time=time(12, 0),
        latitude=0.0,
        longitude=0.0,
        timezone_name="UTC",
    )
    return chart.planets


def format_planet_line(p: PlanetPosition) -> str:
    house_part = f", дом {p.house}" if p.house else ""
    retro = " ℞" if p.retrograde else ""
    return (
        f"{p.glyph} {p.name_ru}: {p.sign_glyph} {p.sign_ru} "
        f"{p.sign_degree:.1f}°{house_part}{retro}"
    )


def summary(chart: NatalChart) -> str:
    """Short textual summary of a chart — used in chat fallbacks."""
    lines = [format_planet_line(p) for p in chart.planets.values()]
    if chart.ascendant is not None:
        asc_sign = ZODIAC_SIGNS[int(chart.ascendant // 30)]
        lines.append(f"ASC: {asc_sign[2]} {asc_sign[1]} {chart.ascendant % 30:.1f}°")
    if chart.midheaven is not None:
        mc_sign = ZODIAC_SIGNS[int(chart.midheaven // 30)]
        lines.append(f"MC: {mc_sign[2]} {mc_sign[1]} {chart.midheaven % 30:.1f}°")
    if chart.aspects:
        lines.append("")
        lines.append("Ключевые аспекты:")
        for asp in chart.aspects[:6]:
            a = chart.planets[asp.planet_a]
            b = chart.planets[asp.planet_b]
            lines.append(
                f"• {a.glyph} {a.name_ru} {asp.name_ru} {b.glyph} {b.name_ru} "
                f"(орб {asp.orb:.1f}°)"
            )
    return "\n".join(lines)


def synastry_score(chart_a: NatalChart, chart_b: NatalChart) -> Tuple[int, List[str]]:
    """A naïve synastry score 0..100 plus a list of highlight strings."""
    score = 50
    highlights: List[str] = []
    weight = {
        "conjunction": 8,
        "trine": 6,
        "sextile": 4,
        "opposition": -4,
        "square": -6,
    }
    for name_a, p_a in chart_a.planets.items():
        for name_b, p_b in chart_b.planets.items():
            diff = abs(p_a.longitude - p_b.longitude) % 360
            if diff > 180:
                diff = 360 - diff
            for asp_en, asp_ru, angle, orb in MAJOR_ASPECTS:
                delta = abs(diff - angle)
                if delta <= orb:
                    score += weight.get(asp_en, 0)
                    if name_a in {"Sun", "Moon", "Venus", "Mars"} and name_b in {
                        "Sun", "Moon", "Venus", "Mars",
                    }:
                        highlights.append(
                            f"{p_a.glyph} {p_a.name_ru} {asp_ru} "
                            f"{p_b.glyph} {p_b.name_ru} (орб {delta:.1f}°)"
                        )
                    break
    score = max(0, min(100, score))
    return score, highlights[:6]
