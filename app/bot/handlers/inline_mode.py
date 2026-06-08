from hashlib import sha1

from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

router = Router(name="inline_mode")

SIGN_HINTS = {
    "aries": "Овна",
    "taurus": "Тельца",
    "gemini": "Близнецов",
    "cancer": "Рака",
    "leo": "Льва",
    "virgo": "Девы",
    "libra": "Весов",
    "scorpio": "Скорпиона",
    "sagittarius": "Стрельца",
    "capricorn": "Козерога",
    "aquarius": "Водолея",
    "pisces": "Рыб",
}


@router.inline_query()
async def inline_query(query: InlineQuery) -> None:
    text = query.query.strip()
    results = [_daily_result(text), _compatibility_result(text)]
    await query.answer([result for result in results if result is not None], cache_time=300, is_personal=False)


def _daily_result(text: str) -> InlineQueryResultArticle | None:
    parts = text.lower().split()
    if len(parts) != 2 or parts[0] != "daily":
        return None
    sign = SIGN_HINTS.get(parts[1])
    if not sign:
        return None
    content = (
        f"⭐ Сегодня для {sign}: хороший день, чтобы заметить важный внутренний сигнал и сделать один "
        "спокойный практический шаг. Астрология носит развлекательный характер."
    )
    return InlineQueryResultArticle(
        id=_stable_id("daily", text),
        title=f"Прогноз на сегодня для {sign}",
        input_message_content=InputTextMessageContent(message_text=content),
        description=content[:100],
    )


def _compatibility_result(text: str) -> InlineQueryResultArticle | None:
    parts = text.lower().split()
    if len(parts) != 3 or parts[0] != "compatibility":
        return None
    sign_a = SIGN_HINTS.get(parts[1])
    sign_b = SIGN_HINTS.get(parts[2])
    if not sign_a or not sign_b:
        return None
    content = (
        f"🔥 Совместимость {sign_a} и {sign_b}: союз строится на обмене разными качествами. "
        "Сильная сторона — интерес друг к другу, зона роста — честно проговаривать ожидания. "
        "Это развлекательная астрологическая интерпретация."
    )
    return InlineQueryResultArticle(
        id=_stable_id("compatibility", text),
        title=f"Совместимость: {sign_a} + {sign_b}",
        input_message_content=InputTextMessageContent(message_text=content),
        description=content[:100],
    )


def _stable_id(prefix: str, value: str) -> str:
    return sha1(f"{prefix}:{value}".encode("utf-8")).hexdigest()
