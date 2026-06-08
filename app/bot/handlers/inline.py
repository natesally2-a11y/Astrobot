from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

from app.astrology.calculations import ChartCalculator

router = Router()
calculator = ChartCalculator()


@router.inline_query()
async def inline_query(query: InlineQuery) -> None:
    text = query.query.strip().lower()
    results = []

    if not text:
        results.append(
            InlineQueryResultArticle(
                id="help",
                title="Stellarium AI — ИИ-астролог",
                description="Попробуйте: compatibility Leo Scorpio или daily Virgo",
                input_message_content=InputTextMessageContent(
                    message_text="🌟 Stellarium AI — персональный ИИ-астролог в Telegram!\n"
                    "Напишите /start для создания натальной карты.",
                ),
            )
        )
    elif text.startswith("compatibility") or text.startswith("совместимость"):
        parts = text.split()
        if len(parts) >= 3:
            sign1 = calculator.sign_from_name(parts[1])
            sign2 = calculator.sign_from_name(parts[2])
            if sign1 and sign2:
                forecast = calculator.generic_compatibility(sign1, sign2)
                results.append(
                    InlineQueryResultArticle(
                        id=f"compat_{sign1}_{sign2}",
                        title=f"Совместимость {sign1} + {sign2}",
                        description=forecast[:80],
                        input_message_content=InputTextMessageContent(message_text=forecast),
                    )
                )
    elif text.startswith("daily") or text.startswith("сегодня"):
        parts = text.split()
        if len(parts) >= 2:
            sign = calculator.sign_from_name(parts[1])
            if sign:
                forecast = calculator.generic_sign_forecast(sign)
                results.append(
                    InlineQueryResultArticle(
                        id=f"daily_{sign}",
                        title=f"Прогноз для {sign}",
                        description=forecast[:80],
                        input_message_content=InputTextMessageContent(message_text=forecast),
                    )
                )

    if not results:
        results.append(
            InlineQueryResultArticle(
                id="default",
                title="Stellarium AI",
                description="Формат: daily Virgo или compatibility Leo Scorpio",
                input_message_content=InputTextMessageContent(
                    message_text="🌟 Попробуйте Stellarium AI — персональный астролог!\n/start",
                ),
            )
        )

    await query.answer(results, cache_time=300, is_personal=True)
