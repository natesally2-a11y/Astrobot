"""Интерпретация астрологических данных через OpenAI GPT.

Если ключ OpenAI не задан, используется детерминированный офлайн-фолбэк,
чтобы бот оставался работоспособным в демо-режиме.
"""
from __future__ import annotations

import logging

from openai import AsyncOpenAI

from app.astrology.calculations import NatalChart, compute_transits
from app.astrology.chart_summary import chart_to_text, transits_to_text
from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Ты — профессиональный астролог с 20-летним опытом. "
    "Анализируй натальную карту, используя:\n"
    "- Позиции планет в знаках и домах\n"
    "- Основные аспекты (соединения, оппозиции, тригоны, квадраты)\n"
    "- Текущие транзиты для прогнозов\n"
    "Стиль: мудрый наставник, но доступный язык. "
    "Длина ответа: 2-3 абзаца максимум. "
    "Фокус на практических советах и позитивном тоне. "
    "Пиши на русском языке. Не упоминай, что ты ИИ. "
    "В конце ненавязчиво напоминай, что прогноз носит развлекательный характер."
)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI | None:
    global _client
    if not settings.openai_api_key:
        return None
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def _complete(user_prompt: str, max_tokens: int = 700) -> str:
    client = _get_client()
    if client is None:
        return _offline_fallback(user_prompt)
    try:
        resp = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.8,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as exc:  # pragma: no cover - сеть
        logger.error("OpenAI error: %s", exc)
        return _offline_fallback(user_prompt)


def _offline_fallback(prompt: str) -> str:
    return (
        "✨ (Демо-режим: ключ OpenAI не настроен)\n\n"
        "Звёзды складываются в интересный узор. На основе вашей карты видно "
        "сочетание сильных сторон и зон роста — обратите внимание на баланс "
        "между действием и рефлексией сегодня.\n\n"
        "Подключите OPENAI_API_KEY, чтобы получать персональные ИИ-интерпретации.\n\n"
        "⚠️ Прогноз носит развлекательный характер."
    )


# ----------------------- Публичные методы интерпретации -----------------------

async def interpret_natal(chart: NatalChart, name: str | None = None) -> str:
    summary = chart_to_text(chart, name)
    prompt = (
        "Проанализируй натальную карту человека. Опиши характер, ключевые "
        "таланты и жизненные задачи. Вот данные карты:\n\n" + summary
    )
    return await _complete(prompt, max_tokens=800)


async def interpret_daily(chart: NatalChart, detailed: bool = False) -> str:
    transits = compute_transits(chart)
    summary = chart_to_text(chart)
    tr = transits_to_text(transits)
    depth = "подробный" if detailed else "краткий"
    prompt = (
        f"Дай {depth} персональный прогноз на сегодня. Учитывай натальную карту "
        f"и текущие транзиты.\n\nНатальная карта:\n{summary}\n\n{tr}"
    )
    return await _complete(prompt, max_tokens=600 if detailed else 350)


async def interpret_period(chart: NatalChart, period: str = "неделю") -> str:
    transits = compute_transits(chart)
    summary = chart_to_text(chart)
    tr = transits_to_text(transits)
    prompt = (
        f"Дай прогноз на {period} вперёд по натальной карте и транзитам. "
        f"Выдели 2-3 ключевые темы периода и практические советы.\n\n"
        f"Натальная карта:\n{summary}\n\n{tr}"
    )
    return await _complete(prompt, max_tokens=700)


async def interpret_transits(chart: NatalChart) -> str:
    transits = compute_transits(chart)
    tr = transits_to_text(transits)
    summary = chart_to_text(chart)
    prompt = (
        "Опиши важные текущие транзиты и их влияние. Что стоит делать и чего "
        f"избегать.\n\nНатальная карта:\n{summary}\n\n{tr}"
    )
    return await _complete(prompt, max_tokens=700)


async def interpret_compatibility(
    chart_a: NatalChart,
    chart_b: NatalChart,
    name_a: str = "Партнёр A",
    name_b: str = "Партнёр B",
) -> str:
    sa = chart_to_text(chart_a, name_a)
    sb = chart_to_text(chart_b, name_b)
    prompt = (
        "Проведи синастрию (анализ совместимости) двух людей. Оцени сильные "
        "стороны союза, потенциальные сложности и дай совет, как укрепить "
        f"отношения. Поставь итоговую оценку совместимости в процентах.\n\n"
        f"=== {name_a} ===\n{sa}\n\n=== {name_b} ===\n{sb}"
    )
    return await _complete(prompt, max_tokens=900)


async def answer_question(chart: NatalChart, question: str) -> str:
    summary = chart_to_text(chart)
    transits = compute_transits(chart)
    tr = transits_to_text(transits)
    prompt = (
        f"Пользователь задаёт вопрос астрологу: «{question}»\n\n"
        f"Ответь, опираясь на его натальную карту и транзиты.\n\n"
        f"Натальная карта:\n{summary}\n\n{tr}"
    )
    return await _complete(prompt, max_tokens=700)


async def interpret_yearly(chart: NatalChart) -> str:
    summary = chart_to_text(chart)
    prompt = (
        "Сделай годовой прогноз (соляр/солнечное возвращение). Выдели главные "
        f"темы года и сферы максимального роста.\n\nНатальная карта:\n{summary}"
    )
    return await _complete(prompt, max_tokens=900)


async def inline_compatibility(sign_a: str, sign_b: str) -> str:
    prompt = (
        f"Кратко (3-4 предложения) опиши совместимость знаков {sign_a} и "
        f"{sign_b}. Добавь подходящий эмодзи в начале."
    )
    return await _complete(prompt, max_tokens=250)


async def inline_daily(sign: str) -> str:
    prompt = (
        f"Кратко (3-4 предложения) дай гороскоп на сегодня для знака {sign}. "
        "Добавь подходящий эмодзи в начале."
    )
    return await _complete(prompt, max_tokens=250)
