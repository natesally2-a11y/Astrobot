"""Inline mode handler for viral sharing."""

import hashlib

from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from app.astrology.ai_interpreter import get_inline_compatibility, get_inline_daily
from app.astrology.calculations import ZODIAC_SIGNS

router = Router()

SIGN_ALIASES = {
    "aries": "Овен", "овен": "Овен",
    "taurus": "Телец", "телец": "Телец",
    "gemini": "Близнецы", "близнецы": "Близнецы",
    "cancer": "Рак", "рак": "Рак",
    "leo": "Лев", "лев": "Лев",
    "virgo": "Дева", "дева": "Дева",
    "libra": "Весы", "весы": "Весы",
    "scorpio": "Скорпион", "скорпион": "Скорпион",
    "sagittarius": "Стрелец", "стрелец": "Стрелец",
    "capricorn": "Козерог", "козерог": "Козерог",
    "aquarius": "Водолей", "водолей": "Водолей",
    "pisces": "Рыбы", "рыбы": "Рыбы",
}


def _resolve_sign(text: str) -> str | None:
    return SIGN_ALIASES.get(text.lower().strip())


def _make_id(*parts: str) -> str:
    raw = "|".join(parts)
    return hashlib.md5(raw.encode()).hexdigest()[:16]


@router.inline_query()
async def inline_handler(inline_query: InlineQuery):
    query = inline_query.query.strip()
    results: list[InlineQueryResultArticle] = []

    if not query:
        results.append(
            InlineQueryResultArticle(
                id="help",
                title="Stellarium AI — ИИ-астролог",
                description="Введите: daily Овен | compatibility Лев Рыбы",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "🌟 <b>Stellarium AI</b> — персональный ИИ-астролог\n\n"
                        "Попробуйте:\n"
                        "@stellarium_ai_bot daily Овен\n"
                        "@stellarium_ai_bot compatibility Лев Скорпион\n\n"
                        "Создайте свою натальную карту: @stellarium_ai_bot"
                    ),
                    parse_mode="HTML",
                ),
            )
        )
        await inline_query.answer(results, cache_time=300)
        return

    parts = query.split()
    command = parts[0].lower()

    if command in ("daily", "today", "день", "сегодня") and len(parts) >= 2:
        sign = _resolve_sign(parts[1])
        if sign:
            try:
                forecast = await get_inline_daily(sign)
            except Exception:
                forecast = f"⭐ Прогноз для {sign} на сегодня скоро будет доступен!"

            results.append(
                InlineQueryResultArticle(
                    id=_make_id("daily", sign),
                    title=f"Прогноз на сегодня: {sign}",
                    description=forecast[:100],
                    input_message_content=InputTextMessageContent(
                        message_text=(
                            f"⭐ <b>Прогноз на сегодня: {sign}</b>\n\n"
                            f"{forecast}\n\n"
                            f"🌟 <i>Stellarium AI — @stellarium_ai_bot</i>"
                        ),
                        parse_mode="HTML",
                    ),
                )
            )

    elif command in ("compatibility", "compat", "совместимость") and len(parts) >= 3:
        sign1 = _resolve_sign(parts[1])
        sign2 = _resolve_sign(parts[2])
        if sign1 and sign2:
            try:
                compat = await get_inline_compatibility(sign1, sign2)
            except Exception:
                compat = f"Совместимость {sign1} и {sign2} — анализ скоро!"

            results.append(
                InlineQueryResultArticle(
                    id=_make_id("compat", sign1, sign2),
                    title=f"Совместимость: {sign1} + {sign2}",
                    description=compat[:100],
                    input_message_content=InputTextMessageContent(
                        message_text=(
                            f"💕 <b>Совместимость: {sign1} + {sign2}</b>\n\n"
                            f"{compat}\n\n"
                            f"🌟 <i>Stellarium AI — @stellarium_ai_bot</i>"
                        ),
                        parse_mode="HTML",
                    ),
                )
            )

    if not results:
        for sign in ZODIAC_SIGNS[:4]:
            results.append(
                InlineQueryResultArticle(
                    id=_make_id("suggest", sign),
                    title=f"Прогноз для {sign}",
                    description=f"Узнать прогноз на сегодня для {sign}",
                    input_message_content=InputTextMessageContent(
                        message_text=(
                            f"⭐ Хочу узнать прогноз для {sign}!\n\n"
                            f"🌟 @stellarium_ai_bot"
                        ),
                    ),
                )
            )

    await inline_query.answer(results, cache_time=60)
