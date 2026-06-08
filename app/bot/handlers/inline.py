"""Inline-режим для вирусного роста: совместимость и гороскоп по знаку."""
from __future__ import annotations

import hashlib

from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from app.astrology.ai_interpreter import inline_compatibility, inline_daily
from app.astrology.constants import ZODIAC_EN, ZODIAC_SIGNS

router = Router(name="inline")

# Сопоставление вариантов написания знака -> русское имя
_SIGN_MAP: dict[str, str] = {}
for _ru, _en in zip(ZODIAC_SIGNS, ZODIAC_EN):
    _SIGN_MAP[_ru.lower()] = _ru
    _SIGN_MAP[_en.lower()] = _ru


def _normalize_sign(token: str) -> str | None:
    return _SIGN_MAP.get(token.strip().lower())


def _result_id(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _hint_article(article_id: str = "hint") -> InlineQueryResultArticle:
    return InlineQueryResultArticle(
        id=article_id,
        title="Stellarium AI — как пользоваться",
        description="daily Лев  •  compatibility Лев Скорпион",
        input_message_content=InputTextMessageContent(
            message_text="🔮 Stellarium AI: наберите «daily Лев» или "
            "«compatibility Лев Скорпион»"
        ),
    )


@router.inline_query()
async def inline_handler(query: InlineQuery) -> None:
    parts = query.query.strip().split()
    results: list[InlineQueryResultArticle] = []

    if not parts:
        await query.answer([_hint_article()], cache_time=10, is_personal=True)
        return

    mode = parts[0].lower()

    if mode in ("compatibility", "совместимость") and len(parts) >= 3:
        s1 = _normalize_sign(parts[1])
        s2 = _normalize_sign(parts[2])
        if s1 and s2:
            answer = await inline_compatibility(s1, s2)
            body = f"💞 Совместимость {s1} и {s2}:\n\n{answer}"
            results.append(
                InlineQueryResultArticle(
                    id=_result_id(body),
                    title=f"Совместимость: {s1} + {s2}",
                    description=answer[:100],
                    input_message_content=InputTextMessageContent(message_text=body),
                )
            )
    elif mode in ("daily", "today", "гороскоп") and len(parts) >= 2:
        s = _normalize_sign(parts[1])
        if s:
            answer = await inline_daily(s)
            body = f"⭐ {s} — сегодня:\n\n{answer}"
            results.append(
                InlineQueryResultArticle(
                    id=_result_id(body),
                    title=f"Гороскоп на сегодня: {s}",
                    description=answer[:100],
                    input_message_content=InputTextMessageContent(message_text=body),
                )
            )

    if not results:
        results.append(_hint_article("no-match"))

    await query.answer(results, cache_time=30, is_personal=True)
