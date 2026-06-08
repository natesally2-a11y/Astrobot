"""
Inline mode handler for viral growth.
Usage: @stellarium_bot daily Дева
       @stellarium_bot compatibility Лев Скорпион
"""
from __future__ import annotations

import hashlib
from aiogram import Router
from aiogram.types import (
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent,
)
from app.astrology.ai_interpreter import get_inline_forecast, get_inline_compatibility
from app.astrology.calculations import ZODIAC_SIGNS

router = Router(name="inline")

ZODIAC_EN_TO_RU = {
    "aries": "Овен", "taurus": "Телец", "gemini": "Близнецы",
    "cancer": "Рак", "leo": "Лев", "virgo": "Дева",
    "libra": "Весы", "scorpio": "Скорпион", "sagittarius": "Стрелец",
    "capricorn": "Козерог", "aquarius": "Водолей", "pisces": "Рыбы",
    "овен": "Овен", "телец": "Телец", "близнецы": "Близнецы",
    "рак": "Рак", "лев": "Лев", "дева": "Дева",
    "весы": "Весы", "скорпион": "Скорпион", "стрелец": "Стрелец",
    "козерог": "Козерог", "водолей": "Водолей", "рыбы": "Рыбы",
}


@router.inline_query()
async def inline_handler(inline_query: InlineQuery):
    query = inline_query.query.strip().lower()
    results = []

    if not query:
        results = _get_help_results()
    elif query.startswith("daily ") or query.startswith("прогноз "):
        parts = query.split(None, 1)
        if len(parts) > 1:
            sign = _resolve_sign(parts[1].strip())
            if sign:
                text = await get_inline_forecast(sign)
                results = [_make_article(
                    id=f"daily_{sign}",
                    title=f"☀️ Прогноз для {sign}",
                    description=text[:100] + "...",
                    text=f"☀️ <b>Прогноз для {sign} на сегодня</b>\n\n{text}\n\n<i>via @stellarium_ai_bot</i>",
                )]

    elif query.startswith("compatibility ") or query.startswith("совместимость "):
        parts = query.split(None, 2)
        if len(parts) >= 3:
            sign1 = _resolve_sign(parts[1].strip())
            sign2 = _resolve_sign(parts[2].strip())
            if sign1 and sign2:
                text = await get_inline_compatibility(sign1, sign2)
                results = [_make_article(
                    id=f"compat_{sign1}_{sign2}",
                    title=f"💕 {sign1} & {sign2}",
                    description=text[:100] + "...",
                    text=f"💕 <b>Совместимость {sign1} и {sign2}</b>\n\n{text}\n\n<i>via @stellarium_ai_bot</i>",
                )]
    else:
        sign = _resolve_sign(query)
        if sign:
            text = await get_inline_forecast(sign)
            results = [_make_article(
                id=f"sign_{sign}",
                title=f"🌟 {sign} — прогноз",
                description=text[:100] + "...",
                text=f"🌟 <b>{sign} — прогноз на сегодня</b>\n\n{text}\n\n<i>via @stellarium_ai_bot</i>",
            )]

    await inline_query.answer(results, cache_time=300, is_personal=False)


def _resolve_sign(text: str) -> str | None:
    text_lower = text.lower().strip()
    return ZODIAC_EN_TO_RU.get(text_lower)


def _make_article(id: str, title: str, description: str, text: str) -> InlineQueryResultArticle:
    return InlineQueryResultArticle(
        id=hashlib.md5(id.encode()).hexdigest(),
        title=title,
        description=description,
        input_message_content=InputTextMessageContent(
            message_text=text,
            parse_mode="HTML",
        ),
    )


def _get_help_results() -> list[InlineQueryResultArticle]:
    examples = [
        ("daily Дева", "☀️ Прогноз по знаку", "Пример: @stellarium_bot daily Дева"),
        ("compatibility Лев Скорпион", "💕 Совместимость знаков", "Пример: @stellarium_bot compatibility Лев Скорпион"),
    ]
    return [
        _make_article(
            id=f"help_{cmd}",
            title=title,
            description=desc,
            text=f"<b>{title}</b>\n\nКоманда: {cmd}\n\nИспользуйте @stellarium_ai_bot для астрологических прогнозов!",
        )
        for cmd, title, desc in examples
    ]
