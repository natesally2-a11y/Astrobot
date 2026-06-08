from __future__ import annotations

from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

router = Router(name=__name__)

SIGN_HINTS = {
    "aries": "день быстрых решений и инициативы",
    "taurus": "фокус на стабильности и практичности",
    "gemini": "удачны переговоры и обмен идеями",
    "cancer": "важно беречь эмоциональный ресурс",
    "leo": "время проявляться и брать лидерство",
    "virgo": "сильны аналитика и внимание к деталям",
    "libra": "ключ к успеху — партнёрства и баланс",
    "scorpio": "глубокие трансформации и честность",
    "sagittarius": "рост через обучение и масштаб",
    "capricorn": "дисциплина принесёт заметный результат",
    "aquarius": "полезно тестировать новые идеи",
    "pisces": "интуиция помогает выбрать верный вектор",
}


@router.inline_query()
async def inline_query_handler(query: InlineQuery) -> None:
    text = (query.query or "").strip().lower()
    results: list[InlineQueryResultArticle] = []

    if text.startswith("compatibility"):
        _, *parts = text.split()
        left = parts[0] if len(parts) > 0 else "aries"
        right = parts[1] if len(parts) > 1 else "libra"
        content = (
            f"💞 Совместимость {left.title()} + {right.title()}\n"
            "Пара может быть очень яркой при уважении личных границ и честной коммуникации.\n"
            "Для персонального синастрического анализа откройте @stellarium_ai_bot."
        )
        results.append(
            InlineQueryResultArticle(
                id="compatibility",
                title=f"Совместимость {left.title()} и {right.title()}",
                description="Быстрый вирусный preview по знакам",
                input_message_content=InputTextMessageContent(message_text=content),
            )
        )
    elif text.startswith("daily"):
        _, *parts = text.split()
        sign = parts[0] if parts else "virgo"
        hint = SIGN_HINTS.get(sign, "хороший день для спокойных, последовательных шагов")
        content = (
            f"⭐ Сегодня для {sign.title()}: {hint}.\n"
            "Это краткий публичный формат. Персональный прогноз с учётом вашей карты — в @stellarium_ai_bot."
        )
        results.append(
            InlineQueryResultArticle(
                id="daily",
                title=f"Daily для {sign.title()}",
                description="Короткий прогноз по знаку",
                input_message_content=InputTextMessageContent(message_text=content),
            )
        )
    else:
        results.append(
            InlineQueryResultArticle(
                id="about",
                title="Stellarium AI",
                description="Пример: daily virgo / compatibility leo scorpio",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "Используйте inline-запросы:\n"
                        "• @stellarium_ai_bot daily virgo\n"
                        "• @stellarium_ai_bot compatibility leo scorpio"
                    )
                ),
            )
        )

    await query.answer(results=results, cache_time=30, is_personal=True)
