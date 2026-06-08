from dataclasses import dataclass, field
from datetime import date, datetime, time, timezone as dt_timezone
from typing import Any

import ephem

ZODIAC_SIGNS = [
    "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
    "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы",
]

PLANET_BODIES = {
    "Солнце": ephem.Sun,
    "Луна": ephem.Moon,
    "Меркурий": ephem.Mercury,
    "Венера": ephem.Venus,
    "Марс": ephem.Mars,
    "Юпитер": ephem.Jupiter,
    "Сатурн": ephem.Saturn,
    "Уран": ephem.Uranus,
    "Нептун": ephem.Neptune,
    "Плутон": ephem.Pluto,
}

ASPECTS = {
    0: "соединение",
    60: "секстиль",
    90: "квадрат",
    120: "тригон",
    180: "оппозиция",
}

SIGN_EMOJI = {
    "Овен": "♈", "Телец": "♉", "Близнецы": "♊", "Рак": "♋",
    "Лев": "♌", "Дева": "♍", "Весы": "♎", "Скорпион": "♏",
    "Стрелец": "♐", "Козерог": "♑", "Водолей": "♒", "Рыбы": "♓",
}


@dataclass
class PlanetPosition:
    name: str
    longitude: float
    sign: str
    sign_degree: float
    house: int | None = None
    retrograde: bool = False


@dataclass
class Aspect:
    planet1: str
    planet2: str
    aspect_type: str
    orb: float


@dataclass
class NatalChart:
    planets: list[PlanetPosition] = field(default_factory=list)
    houses: list[float] = field(default_factory=list)
    ascendant: float = 0.0
    ascendant_sign: str = ""
    midheaven: float = 0.0
    aspects: list[Aspect] = field(default_factory=list)
    julian_day: float = 0.0


class ChartCalculator:
    def _longitude_to_sign(self, longitude: float) -> tuple[str, float]:
        lon = longitude % 360
        sign_index = int(lon // 30) % 12
        degree = lon % 30
        return ZODIAC_SIGNS[sign_index], degree

    def _ecliptic_longitude(self, body) -> float:
        import math
        ra = float(body.ra)
        dec = float(body.dec)
        eps = math.radians(23.4392911)
        ra_rad = float(body.ra)
        dec_rad = float(body.dec)
        lon = math.atan2(
            math.sin(ra_rad) * math.cos(eps) + math.tan(dec_rad) * math.sin(eps),
            math.cos(ra_rad),
        )
        return math.degrees(lon) % 360

    def _make_observer(
        self,
        birth_date: date,
        birth_time: time | None,
        latitude: float,
        longitude: float,
        timezone_offset_hours: float,
    ) -> ephem.Observer:
        observer = ephem.Observer()
        observer.lat = str(latitude)
        observer.lon = str(longitude)
        hour = birth_time.hour if birth_time else 12
        minute = birth_time.minute if birth_time else 0
        dt = datetime(
            birth_date.year, birth_date.month, birth_date.day,
            hour, minute,
            tzinfo=dt_timezone.utc,
        )
        utc_dt = dt.timestamp() - timezone_offset_hours * 3600
        observer.date = ephem.Date(utc_dt / 86400.0 + ephem.Date(0))
        return observer

    def _calc_asc_mc(self, observer: ephem.Observer) -> tuple[float, float]:
        import math
        lst = float(observer.sidereal_time())
        lat = math.radians(float(observer.lat))
        obl = math.radians(23.4397)
        y = -math.cos(lst)
        x = math.sin(lst) * math.cos(obl) + math.tan(lat) * math.sin(obl)
        asc_lon = math.degrees(math.atan2(y, x)) % 360
        mc_lon = math.degrees(math.atan2(math.sin(lst), math.cos(lst) * math.cos(obl))) % 360
        return asc_lon, mc_lon

    def _get_house_number(self, longitude: float, ascendant: float) -> int:
        diff = (longitude - ascendant) % 360
        return int(diff // 30) + 1

    def calculate_natal_chart(
        self,
        birth_date: date,
        birth_time: time | None,
        latitude: float,
        longitude: float,
        timezone_offset_hours: float = 3.0,
    ) -> NatalChart:
        observer = self._make_observer(
            birth_date, birth_time, latitude, longitude, timezone_offset_hours
        )
        asc_lon, mc_lon = self._calc_asc_mc(observer)
        asc_sign, _ = self._longitude_to_sign(asc_lon)

        houses = [(asc_lon + i * 30) % 360 for i in range(12)]

        planets: list[PlanetPosition] = []
        for name, body_class in PLANET_BODIES.items():
            body = body_class(observer)
            lon = self._ecliptic_longitude(body)
            sign, degree = self._longitude_to_sign(lon)
            house = self._get_house_number(lon, asc_lon)
            prev = body_class(observer)
            observer.date -= 1.0 / 24.0
            prev.compute(observer)
            observer.date += 1.0 / 24.0
            prev_lon = self._ecliptic_longitude(prev)
            retrograde = (lon - prev_lon) % 360 > 180 if name not in ("Солнце", "Луна") else False
            planets.append(
                PlanetPosition(
                    name=name,
                    longitude=lon,
                    sign=sign,
                    sign_degree=degree,
                    house=house,
                    retrograde=retrograde,
                )
            )

        aspects = self._calculate_aspects(planets)

        return NatalChart(
            planets=planets,
            houses=houses,
            ascendant=asc_lon,
            ascendant_sign=asc_sign,
            midheaven=mc_lon,
            aspects=aspects,
        )

    def calculate_transits(
        self,
        natal_chart: NatalChart,
        transit_date: date | None = None,
    ) -> list[Aspect]:
        if transit_date is None:
            transit_date = date.today()

        observer = ephem.Observer()
        observer.lat = "55.75"
        observer.lon = "37.62"
        observer.date = ephem.Date(datetime(transit_date.year, transit_date.month, transit_date.day))

        transit_planets: list[PlanetPosition] = []
        for name, body_class in PLANET_BODIES.items():
            body = body_class(observer)
            lon = self._ecliptic_longitude(body)
            sign, degree = self._longitude_to_sign(lon)
            transit_planets.append(
                PlanetPosition(name=f"Тр.{name}", longitude=lon, sign=sign, sign_degree=degree)
            )

        aspects: list[Aspect] = []
        for tp in transit_planets:
            for np in natal_chart.planets:
                diff = abs(tp.longitude - np.longitude)
                if diff > 180:
                    diff = 360 - diff
                for aspect_angle, aspect_name in ASPECTS.items():
                    orb = abs(diff - aspect_angle)
                    if orb <= 5:
                        aspects.append(
                            Aspect(
                                planet1=tp.name,
                                planet2=np.name,
                                aspect_type=aspect_name,
                                orb=round(orb, 2),
                            )
                        )
        return aspects

    def _calculate_aspects(self, planets: list[PlanetPosition]) -> list[Aspect]:
        aspects: list[Aspect] = []
        for i, p1 in enumerate(planets):
            for p2 in planets[i + 1 :]:
                diff = abs(p1.longitude - p2.longitude)
                if diff > 180:
                    diff = 360 - diff
                for aspect_angle, aspect_name in ASPECTS.items():
                    orb = abs(diff - aspect_angle)
                    if orb <= 8:
                        aspects.append(
                            Aspect(
                                planet1=p1.name,
                                planet2=p2.name,
                                aspect_type=aspect_name,
                                orb=round(orb, 2),
                            )
                        )
        return aspects

    def chart_to_text(self, chart: NatalChart) -> str:
        lines = [f"Асцендент: {chart.ascendant_sign} ({chart.ascendant:.1f}°)", "", "Планеты:"]
        for p in chart.planets:
            retro = " (R)" if p.retrograde else ""
            house_str = f", дом {p.house}" if p.house else ""
            lines.append(f"  {p.name}: {p.sign} {p.sign_degree:.1f}°{house_str}{retro}")
        if chart.aspects:
            lines.append("\nОсновные аспекты:")
            for a in chart.aspects[:10]:
                lines.append(f"  {a.planet1} {a.aspect_type} {a.planet2} (орб {a.orb}°)")
        return "\n".join(lines)

    def chart_to_dict(self, chart: NatalChart) -> dict[str, Any]:
        return {
            "ascendant_sign": chart.ascendant_sign,
            "ascendant": chart.ascendant,
            "midheaven": chart.midheaven,
            "houses": chart.houses,
            "planets": [
                {
                    "name": p.name,
                    "sign": p.sign,
                    "sign_emoji": SIGN_EMOJI.get(p.sign, ""),
                    "degree": round(p.sign_degree, 2),
                    "longitude": round(p.longitude, 2),
                    "house": p.house,
                    "retrograde": p.retrograde,
                }
                for p in chart.planets
            ],
            "aspects": [
                {"planet1": a.planet1, "planet2": a.planet2, "type": a.aspect_type, "orb": a.orb}
                for a in chart.aspects
            ],
        }

    def sign_from_name(self, sign_name: str) -> str | None:
        mapping = {
            "aries": "Овен", "taurus": "Телец", "gemini": "Близнецы",
            "cancer": "Рак", "leo": "Лев", "virgo": "Дева",
            "libra": "Весы", "scorpio": "Скорпион", "sagittarius": "Стрелец",
            "capricorn": "Козерог", "aquarius": "Водолей", "pisces": "Рыбы",
            "овен": "Овен", "телец": "Телец", "близнецы": "Близнецы",
            "рак": "Рак", "лев": "Лев", "дева": "Дева",
            "весы": "Весы", "скорпион": "Скорпион", "стрелец": "Стрелец",
            "козерог": "Козерог", "водолей": "Водолей", "рыбы": "Рыбы",
        }
        return mapping.get(sign_name.lower())

    def generic_sign_forecast(self, sign: str) -> str:
        emoji = SIGN_EMOJI.get(sign, "⭐")
        forecasts = {
            "Овен": f"{emoji} Сегодня для Овна отличный день для новых начинаний. Марс даёт энергию — используйте её мудро.",
            "Телец": f"{emoji} День стабильности для Тельца. Хорошее время для финансовых решений и заботы о себе.",
            "Близнецы": f"{emoji} Близнецы сегодня в ударе! Общение и обучение принесут неожиданные возможности.",
            "Рак": f"{emoji} Для Рака день эмоциональной глубины. Доверьтесь интуиции в семейных вопросах.",
            "Лев": f"{emoji} Лев сияет сегодня! Творческие проекты и лидерство принесут признание.",
            "Дева": f"{emoji} Дева, сегодня идеальный день для организации и планирования. Детали — ваш союзник.",
            "Весы": f"{emoji} Весы находят гармонию в отношениях. Дипломатия откроет нужные двери.",
            "Скорпион": f"{emoji} Скорпион чувствует трансформацию. Глубокие инсайты ждут вас сегодня.",
            "Стрелец": f"{emoji} Стрелец, день приключений! Расширяйте горизонты — удача на вашей стороне.",
            "Козерог": f"{emoji} Козерог, карьерные возможности на горизонте. Терпение и труд окупятся.",
            "Водолей": f"{emoji} Водолей получает вдохновение для инноваций. Нестандартные идеи сегодня особенно ценны.",
            "Рыбы": f"{emoji} Рыбы погружаются в мир интуиции. Творчество и медитация принесут покой.",
        }
        return forecasts.get(sign, f"{emoji} Сегодня звёзды благоволят знаку {sign}!")

    def generic_compatibility(self, sign1: str, sign2: str) -> str:
        fire = {"Овен", "Лев", "Стрелец"}
        earth = {"Телец", "Дева", "Козерог"}
        air = {"Близнецы", "Весы", "Водолей"}
        water = {"Рак", "Скорпион", "Рыбы"}

        s1, s2 = sign1, sign2
        if s1 in fire and s2 in fire:
            return f"🔥 Совместимость {s1} и {s2}: Страстный и энергичный союз! Оба знака огня понимают друг друга с полуслова."
        if s1 in water and s2 in water:
            return f"💧 Совместимость {s1} и {s2}: Глубокая эмоциональная связь. Вы чувствуете друг друга на интуитивном уровне."
        if s1 in earth and s2 in earth:
            return f"🌍 Совместимость {s1} и {s2}: Стабильный и надёжный союз. Практичность и верность — ваши крепости."
        if s1 in air and s2 in air:
            return f"💨 Совместимость {s1} и {s2}: Интеллектуальный союз! Бесконечные разговоры и общие идеи."
        if (s1 in fire and s2 in air) or (s1 in air and s2 in fire):
            return f"✨ Совместимость {s1} и {s2}: Динамичная пара! Огонь вдохновляет Воздух, Воздух раздувает Огонь."
        if (s1 in water and s2 in earth) or (s1 in earth and s2 in water):
            return f"🌿 Совместимость {s1} и {s2}: Гармоничный союз. Земля даёт опору, Вода — глубину чувств."
        return f"⭐ Совместимость {s1} и {s2}: Интересный союз с потенциалом роста. Различия — ваша сила, если вы готовы учиться друг у друга."
