"""Astrological constants: signs, planets, aspects (Russian labels)."""
from __future__ import annotations

# Zodiac signs in order (0 = Aries). Each spans 30 degrees of the ecliptic.
SIGNS = [
    ("Овен", "Aries", "♈", "Огонь", "Кардинальный", "Марс"),
    ("Телец", "Taurus", "♉", "Земля", "Фиксированный", "Венера"),
    ("Близнецы", "Gemini", "♊", "Воздух", "Мутабельный", "Меркурий"),
    ("Рак", "Cancer", "♋", "Вода", "Кардинальный", "Луна"),
    ("Лев", "Leo", "♌", "Огонь", "Фиксированный", "Солнце"),
    ("Дева", "Virgo", "♍", "Земля", "Мутабельный", "Меркурий"),
    ("Весы", "Libra", "♎", "Воздух", "Кардинальный", "Венера"),
    ("Скорпион", "Scorpio", "♏", "Вода", "Фиксированный", "Плутон"),
    ("Стрелец", "Sagittarius", "♐", "Огонь", "Мутабельный", "Юпитер"),
    ("Козерог", "Capricorn", "♑", "Земля", "Кардинальный", "Сатурн"),
    ("Водолей", "Aquarius", "♒", "Воздух", "Фиксированный", "Уран"),
    ("Рыбы", "Pisces", "♓", "Вода", "Мутабельный", "Нептун"),
]

SIGN_NAMES_RU = [s[0] for s in SIGNS]
SIGN_GLYPHS = [s[2] for s in SIGNS]

# Map common English sign names (used by inline mode) to index.
SIGN_ALIASES = {}
for _idx, _s in enumerate(SIGNS):
    SIGN_ALIASES[_s[0].lower()] = _idx          # Russian
    SIGN_ALIASES[_s[1].lower()] = _idx          # English
    SIGN_ALIASES[_s[2]] = _idx                  # glyph
# A few extra common spellings
SIGN_ALIASES.update(
    {
        "стрелец": 8,
        "скорпион": 7,
        "водолей": 10,
        "scorpius": 7,
        "aquarius": 10,
    }
)

# Planets / points with their Swiss Ephemeris ids (filled lazily to avoid hard
# dependency on swisseph at import time for the constants module).
# (key, russian, glyph)
PLANETS = [
    ("sun", "Солнце", "☉"),
    ("moon", "Луна", "☽"),
    ("mercury", "Меркурий", "☿"),
    ("venus", "Венера", "♀"),
    ("mars", "Марс", "♂"),
    ("jupiter", "Юпитер", "♃"),
    ("saturn", "Сатурн", "♄"),
    ("uranus", "Уран", "♅"),
    ("neptune", "Нептун", "♆"),
    ("pluto", "Плутон", "♇"),
    ("north_node", "Сев. узел", "☊"),
    ("chiron", "Хирон", "⚷"),
]

PLANET_NAMES_RU = {p[0]: p[1] for p in PLANETS}
PLANET_GLYPHS = {p[0]: p[2] for p in PLANETS}

# Major aspects: name, angle, default orb, glyph
ASPECTS = [
    ("Соединение", "conjunction", 0.0, 8.0, "☌"),
    ("Оппозиция", "opposition", 180.0, 8.0, "☍"),
    ("Трин", "trine", 120.0, 7.0, "△"),
    ("Квадрат", "square", 90.0, 6.0, "□"),
    ("Секстиль", "sextile", 60.0, 5.0, "✶"),
]

ELEMENT_COLORS = {
    "Огонь": "#e25822",
    "Земля": "#5b8a3c",
    "Воздух": "#d9b54a",
    "Вода": "#3a7ca5",
}

ASPECT_COLORS = {
    "conjunction": "#9b59b6",
    "opposition": "#c0392b",
    "trine": "#27ae60",
    "square": "#e67e22",
    "sextile": "#2980b9",
}


def sign_index(value: str) -> int | None:
    """Resolve a sign from arbitrary user input; returns index or None."""
    if value is None:
        return None
    return SIGN_ALIASES.get(value.strip().lower())


def degree_to_sign(longitude: float) -> tuple[int, float]:
    """Convert an absolute ecliptic longitude to (sign_index, degrees_in_sign)."""
    longitude = longitude % 360.0
    idx = int(longitude // 30)
    deg_in_sign = longitude - idx * 30
    return idx, deg_in_sign
