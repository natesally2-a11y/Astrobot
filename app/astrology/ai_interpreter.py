"""GPT-powered astrological interpretation with an offline mock fallback."""
from __future__ import annotations

import logging
from typing import List, Optional

from app.astrology.calculations import Aspect, NatalChart
from app.astrology.constants import SIGN_NAMES_RU
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
    "Пиши на русском языке. "
    "Помни: астрология носит развлекательный характер, не давай медицинских, "
    "финансовых или юридических указаний как руководство к действию."
)

_DISCLAIMER = "✨ _Прогноз носит развлекательный характер._"


def chart_summary(chart: NatalChart, *, name: Optional[str] = None) -> str:
    """Compact textual summary of a chart fed into the LLM prompt."""
    lines: List[str] = []
    if name:
        lines.append(f"Имя: {name}")
    if chart.ascendant_sign is not None:
        lines.append(f"Асцендент: {SIGN_NAMES_RU[chart.ascendant_sign]}")
    lines.append("Планеты:")
    for p in chart.planets:
        house = f", дом {p.house}" if p.house else ""
        lines.append(f"  - {p.name}: {p.position_str}{house}")
    if chart.aspects:
        lines.append("Ключевые аспекты:")
        for asp in chart.aspects[:10]:
            lines.append(f"  - {asp.description}")
    return "\n".join(lines)


def _aspects_summary(aspects: List[Aspect], limit: int = 8) -> str:
    return "\n".join(f"  - {a.description}" for a in aspects[:limit]) or "  - значимых аспектов нет"


async def _complete(user_prompt: str, *, max_tokens: int = 600) -> str:
    """Call the OpenAI chat completion API (or return a mock response)."""
    if settings.openai_mock or not settings.openai_api_key:
        return _mock_response(user_prompt)

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        resp = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.85,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("OpenAI request failed: %s", exc)
        return (
            "Звёзды сейчас отвечают неохотно — сервис ИИ временно недоступен. "
            "Попробуйте, пожалуйста, чуть позже."
        )


def _mock_response(prompt: str) -> str:
    """Deterministic offline response so the bot is fully functional without a key."""
    head = prompt.strip().splitlines()[0] if prompt.strip() else "Анализ"
    return (
        "🌙 *Демо-режим интерпретации* (OPENAI_MOCK=true).\n\n"
        "Ваша карта раскрывает яркое сочетание энергий: внутренняя сила стремится "
        "к самовыражению, а интуиция помогает чувствовать верный момент. Сейчас удачное "
        "время, чтобы прислушаться к себе и сделать шаг к давней цели.\n\n"
        "Совет дня: уделите внимание балансу между действием и отдыхом — гармония "
        "приходит к тем, кто умеет ждать и действовать вовремя.\n\n"
        f"_(Контекст запроса: {head[:80]})_\n\n" + _DISCLAIMER
    )


async def interpret_natal(chart: NatalChart, name: Optional[str] = None) -> str:
    prompt = (
        "Сделай анализ натальной карты человека: характер, таланты и жизненные задачи.\n\n"
        f"{chart_summary(chart, name=name)}"
    )
    return await _complete(prompt, max_tokens=700)


async def interpret_daily(chart: NatalChart, transits: List[Aspect], name: Optional[str] = None) -> str:
    prompt = (
        "Дай персональный прогноз на сегодня на основе натальной карты и текущих транзитов. "
        "Что важно учесть именно сегодня?\n\n"
        f"{chart_summary(chart, name=name)}\n\n"
        "Текущие транзиты к натальным планетам:\n"
        f"{_aspects_summary(transits)}"
    )
    return await _complete(prompt, max_tokens=500)


async def interpret_weekly(chart: NatalChart, transits: List[Aspect], name: Optional[str] = None) -> str:
    prompt = (
        "Дай прогноз на ближайшую неделю на основе натальной карты и текущих транзитов. "
        "Опиши главные темы недели и практические рекомендации.\n\n"
        f"{chart_summary(chart, name=name)}\n\n"
        "Транзиты периода:\n"
        f"{_aspects_summary(transits, limit=12)}"
    )
    return await _complete(prompt, max_tokens=650)


async def interpret_transits(chart: NatalChart, transits: List[Aspect], name: Optional[str] = None) -> str:
    prompt = (
        "Опиши важные текущие транзиты и их влияние. Выдели самые значимые и дай советы.\n\n"
        f"{chart_summary(chart, name=name)}\n\n"
        "Транзиты:\n"
        f"{_aspects_summary(transits, limit=12)}"
    )
    return await _complete(prompt, max_tokens=650)


async def interpret_compatibility(
    chart_a: NatalChart,
    chart_b: NatalChart,
    name_a: Optional[str] = None,
    name_b: Optional[str] = None,
) -> str:
    # Cross-aspects between the two charts (synastry).
    synastry: List[Aspect] = []
    from app.astrology.constants import ASPECTS  # reuse aspect definitions / orbs

    for p1 in chart_a.planets:
        for p2 in chart_b.planets:
            diff = abs(p1.longitude - p2.longitude) % 360.0
            if diff > 180.0:
                diff = 360.0 - diff
            for nm, key, angle, orb, _g in ASPECTS:
                if abs(diff - angle) <= orb:
                    synastry.append(
                        Aspect(p1.key, p2.key, nm, key, angle, round(abs(diff - angle), 2))
                    )
                    break
    synastry.sort(key=lambda a: a.orb)

    prompt = (
        "Проанализируй совместимость двух людей (синастрия). Опиши сильные стороны союза, "
        "возможные сложности и дай рекомендации.\n\n"
        f"Партнёр A ({name_a or 'A'}):\n{chart_summary(chart_a)}\n\n"
        f"Партнёр B ({name_b or 'B'}):\n{chart_summary(chart_b)}\n\n"
        "Межкартовые аспекты (синастрия):\n"
        f"{_aspects_summary(synastry, limit=12)}"
    )
    return await _complete(prompt, max_tokens=750)


async def answer_question(chart: NatalChart, question: str, name: Optional[str] = None) -> str:
    prompt = (
        f"Пользователь задаёт вопрос астрологу: «{question}»\n\n"
        "Ответь, опираясь на его натальную карту.\n\n"
        f"{chart_summary(chart, name=name)}"
    )
    return await _complete(prompt, max_tokens=600)
