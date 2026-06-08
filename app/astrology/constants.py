"""Астрологические константы: знаки, планеты, аспекты."""
from __future__ import annotations

ZODIAC_SIGNS = [
    "Овен",
    "Телец",
    "Близнецы",
    "Рак",
    "Лев",
    "Дева",
    "Весы",
    "Скорпион",
    "Стрелец",
    "Козерог",
    "Водолей",
    "Рыбы",
]

ZODIAC_SYMBOLS = [
    "♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓",
]

ZODIAC_EN = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

ELEMENTS = {
    "Огонь": [0, 4, 8],
    "Земля": [1, 5, 9],
    "Воздух": [2, 6, 10],
    "Вода": [3, 7, 11],
}

# Планеты: ключ -> (русское имя, символ)
PLANETS = {
    "sun": ("Солнце", "☉"),
    "moon": ("Луна", "☽"),
    "mercury": ("Меркурий", "☿"),
    "venus": ("Венера", "♀"),
    "mars": ("Марс", "♂"),
    "jupiter": ("Юпитер", "♃"),
    "saturn": ("Сатурн", "♄"),
    "uranus": ("Уран", "♅"),
    "neptune": ("Нептун", "♆"),
    "pluto": ("Плутон", "♇"),
    "north_node": ("Сев. узел", "☊"),
}

# Аспекты: имя -> (угол, орбис, символ)
ASPECTS = {
    "Соединение": (0, 8, "☌"),
    "Оппозиция": (180, 8, "☍"),
    "Тригон": (120, 7, "△"),
    "Квадрат": (90, 6, "□"),
    "Секстиль": (60, 5, "✶"),
}


def sign_index(longitude: float) -> int:
    """Индекс знака зодиака (0..11) по эклиптической долготе."""
    return int((longitude % 360) // 30)


def degree_in_sign(longitude: float) -> float:
    """Градус внутри знака (0..30)."""
    return (longitude % 360) % 30


def sign_name(longitude: float) -> str:
    return ZODIAC_SIGNS[sign_index(longitude)]


def element_of_sign(idx: int) -> str:
    for element, signs in ELEMENTS.items():
        if idx in signs:
            return element
    return ""
