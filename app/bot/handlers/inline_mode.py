"""Inline mode: @stellarium_bot daily Leo / compatibility Leo Scorpio."""
from __future__ import annotations

import hashlib

from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

router = Router(name="inline")


ZODIAC_RU = {
    "aries": "Овен", "taurus": "Телец", "gemini": "Близнецы", "cancer": "Рак",
    "leo": "Лев", "virgo": "Дева", "libra": "Весы", "scorpio": "Скорпион",
    "sagittarius": "Стрелец", "capricorn": "Козерог",
    "aquarius": "Водолей", "pisces": "Рыбы",
    "овен": "Овен", "телец": "Телец", "близнецы": "Близнецы", "рак": "Рак",
    "лев": "Лев", "дева": "Дева", "весы": "Весы", "скорпион": "Скорпион",
    "стрелец": "Стрелец", "козерог": "Козерог",
    "водолей": "Водолей", "рыбы": "Рыбы",
}

COMPAT_TEXTS = {
    ("Лев", "Скорпион"):
        "🔥 Страстный союз: огонь и вода создают магнетическое притяжение, "
        "но требуют взаимного уважения и пространства.",
}


def _norm(sign: str) -> str | None:
    return ZODIAC_RU.get(sign.strip().lower())


def _daily_text(sign: str) -> str:
    return (
        f"⭐ Сегодня для знака {sign}: отличное время для коротких, но смелых "
        f"решений. Луна благоволит вашим планам — действуйте, доверяя интуиции."
    )


def _compat_text(a: str, b: str) -> str:
    key = (a, b) if (a, b) in COMPAT_TEXTS else (b, a) if (b, a) in COMPAT_TEXTS else None
    if key is not None:
        return f"Совместимость {a} и {b}:\n{COMPAT_TEXTS[key]}"
    return (
        f"Совместимость {a} и {b}: интересная пара! Сильная сторона — обмен "
        "энергиями, точка роста — учиться слышать друг друга."
    )


def _hash_id(*parts: str) -> str:
    return hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()[:16]


@router.inline_query()
async def inline_query(query: InlineQuery) -> None:
    text = (query.query or "").strip().lower()
    results: list[InlineQueryResultArticle] = []

    if not text:
        results.append(
            InlineQueryResultArticle(
                id="hint",
                title="Используйте: daily <знак> или compatibility <знак> <знак>",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "🌌 Stellarium AI — попробуйте:\n"
                        "@{bot} daily Лев\n"
                        "@{bot} compatibility Лев Скорпион"
                    )
                ),
            )
        )
    else:
        parts = text.split()
        if parts[0] in {"daily", "today", "сегодня"} and len(parts) >= 2:
            sign = _norm(parts[1])
            if sign:
                txt = _daily_text(sign)
                results.append(
                    InlineQueryResultArticle(
                        id=_hash_id("daily", sign),
                        title=f"Прогноз на сегодня — {sign}",
                        description=txt[:80],
                        input_message_content=InputTextMessageContent(message_text=txt),
                    )
                )
        elif parts[0] in {"compatibility", "compat", "совместимость"} and len(parts) >= 3:
            a = _norm(parts[1])
            b = _norm(parts[2])
            if a and b:
                txt = _compat_text(a, b)
                results.append(
                    InlineQueryResultArticle(
                        id=_hash_id("compat", a, b),
                        title=f"Совместимость {a} и {b}",
                        description=txt[:80],
                        input_message_content=InputTextMessageContent(message_text=txt),
                    )
                )

    if not results:
        results.append(
            InlineQueryResultArticle(
                id="empty",
                title="Не понял запрос — попробуйте 'daily Лев' или 'compatibility Лев Скорпион'",
                input_message_content=InputTextMessageContent(
                    message_text="🌌 Узнайте больше в @stellarium_ai_bot"
                ),
            )
        )

    await query.answer(results, cache_time=60, is_personal=False)
