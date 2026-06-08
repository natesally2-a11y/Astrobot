from __future__ import annotations

from aiogram import F, Router
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

router = Router(name="inline-mode")


@router.inline_query(F.query.regexp(r"^daily\s+\S+"))
async def inline_daily(query: InlineQuery) -> None:
    _, sign = query.query.split(maxsplit=1)
    text = (
        f"Сегодня для {sign.title()}: ⭐ День подходит для спокойного прогресса. "
        "Сфокусируйтесь на 1-2 главных задачах и не распыляйтесь."
    )
    result = InlineQueryResultArticle(
        id="daily_result",
        title=f"Ежедневный прогноз: {sign.title()}",
        description="Короткий прогноз в inline-режиме",
        input_message_content=InputTextMessageContent(message_text=text),
    )
    await query.answer([result], cache_time=60, is_personal=True)


@router.inline_query(F.query.regexp(r"^compatibility\s+\S+\s+\S+"))
async def inline_compatibility(query: InlineQuery) -> None:
    _, first, second = query.query.split(maxsplit=2)
    text = (
        f"Совместимость {first.title()} и {second.title()}: 🔥 "
        "Пара с сильной эмоциональной динамикой и потенциалом роста через честный диалог."
    )
    result = InlineQueryResultArticle(
        id="compat_result",
        title=f"Совместимость: {first.title()} + {second.title()}",
        description="Короткий разбор пары в inline-режиме",
        input_message_content=InputTextMessageContent(message_text=text),
    )
    await query.answer([result], cache_time=60, is_personal=True)

