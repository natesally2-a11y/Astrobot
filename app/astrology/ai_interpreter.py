"""GPT-powered astrological interpretation layer."""

from __future__ import annotations

import logging
from typing import Optional

from openai import AsyncOpenAI, OpenAIError

from app.astrology.calculations import (
    Aspect,
    NatalChart,
    PLANET_NAMES_RU,
    summarize_chart,
)
from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Ты — профессиональный астролог Stellarium AI с 20-летним опытом.\n"
    "Анализируй натальную карту, используя:\n"
    "- Позиции планет в знаках и домах\n"
    "- Основные аспекты (соединения, оппозиции, тригоны, квадраты)\n"
    "- Текущие транзиты для прогнозов\n\n"
    "Стиль: мудрый наставник, доступный, тёплый язык, без эзотерического жаргона.\n"
    "Структура ответа: 2–3 коротких абзаца, фокус на практических советах и"
    " позитивном тоне.\n"
    "В конце ответа всегда напоминай в одной короткой строке, что прогноз носит"
    " развлекательный характер."
)


_client: Optional[AsyncOpenAI] = None


def _get_client() -> Optional[AsyncOpenAI]:
    global _client
    if not settings.openai_api_key:
        return None
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def _ask_llm(prompt: str, *, max_tokens: int = 600) -> str:
    client = _get_client()
    if client is None:
        return _fallback_response(prompt)
    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
            max_tokens=max_tokens,
        )
        text = (response.choices[0].message.content or "").strip()
        if not text:
            return _fallback_response(prompt)
        return text
    except OpenAIError as exc:
        logger.warning("OpenAI request failed: %s", exc)
        return _fallback_response(prompt)


def _fallback_response(prompt: str) -> str:
    return (
        "Сейчас не удаётся подключиться к ИИ-астрологу, но звёзды всё равно с"
        " тобой. Сохраняй спокойствие, наблюдай за внутренними импульсами —"
        " они подскажут лучший шаг.\n\n"
        "Попробуй задать вопрос чуть позже.\n\n"
        "⚠️ Прогноз носит развлекательный характер."
    )


async def interpret_natal(chart: NatalChart, user_name: Optional[str] = None) -> str:
    summary = summarize_chart(chart, lang="ru")
    prompt = (
        f"Сделай интерпретацию натальной карты пользователя"
        f"{' ' + user_name if user_name else ''}.\n"
        f"Опиши характер, сильные стороны и главные жизненные задачи."
        f"\n\nДанные карты:\n{summary}"
    )
    return await _ask_llm(prompt, max_tokens=700)


async def interpret_daily(
    chart: NatalChart, transits: list[Aspect], user_name: Optional[str] = None
) -> str:
    transit_lines = [t.formatted(lang="ru") for t in transits[:8]] or [
        "Сегодня нет острых транзитов — спокойный фон."
    ]
    summary = summarize_chart(chart, lang="ru")
    prompt = (
        f"Сформируй персональный прогноз на сегодня"
        f"{' для ' + user_name if user_name else ''}.\n"
        f"Учитывай натальные позиции и текущие транзиты.\n"
        f"\nНатальная карта (сокращённо):\n{summary}\n"
        f"\nТекущие транзиты:\n" + "\n".join(f"- {line}" for line in transit_lines)
    )
    return await _ask_llm(prompt, max_tokens=500)


async def interpret_weekly(
    chart: NatalChart, transits: list[Aspect], user_name: Optional[str] = None
) -> str:
    transit_lines = [t.formatted(lang="ru") for t in transits[:12]] or [
        "Транзиты недели спокойные."
    ]
    summary = summarize_chart(chart, lang="ru")
    prompt = (
        f"Составь прогноз на ближайшую неделю"
        f"{' для ' + user_name if user_name else ''}.\n"
        f"Выдели 2–3 ключевые темы недели.\n\n"
        f"Натальная карта:\n{summary}\n\n"
        f"Активные транзиты недели:\n" + "\n".join(f"- {line}" for line in transit_lines)
    )
    return await _ask_llm(prompt, max_tokens=700)


async def interpret_compatibility(
    chart_a: NatalChart,
    chart_b: NatalChart,
    cross_aspects: list[Aspect],
    name_a: Optional[str] = None,
    name_b: Optional[str] = None,
) -> str:
    cross_lines = [a.formatted(lang="ru") for a in cross_aspects[:12]] or [
        "Заметных синастрических аспектов нет."
    ]
    prompt = (
        f"Оцени совместимость партнёров {name_a or 'A'} и {name_b or 'B'}.\n"
        f"Дай 2–3 абзаца: сильные стороны союза, точки роста, практические советы."
        f"\n\nКлючевые межкартные аспекты:\n"
        + "\n".join(f"- {line}" for line in cross_lines)
    )
    return await _ask_llm(prompt, max_tokens=700)


async def interpret_question(
    chart: NatalChart, transits: list[Aspect], question: str, user_name: Optional[str] = None
) -> str:
    summary = summarize_chart(chart, lang="ru")
    transit_lines = [t.formatted(lang="ru") for t in transits[:6]] or ["спокойный фон"]
    prompt = (
        f"Пользователь{' ' + user_name if user_name else ''} спрашивает:"
        f" «{question}»\n\n"
        f"Натальная карта:\n{summary}\n\n"
        f"Текущие транзиты:\n" + "\n".join(f"- {line}" for line in transit_lines) +
        "\n\nОтветь как личный астролог, опираясь на карту и транзиты."
    )
    return await _ask_llm(prompt, max_tokens=600)


async def interpret_transit(transits: list[Aspect]) -> str:
    if not transits:
        return (
            "Сегодня и в ближайшие дни — спокойный астрологический фон. Хороший"
            " момент для отдыха и планов.\n\n⚠️ Прогноз носит развлекательный"
            " характер."
        )
    transit_lines = [t.formatted(lang="ru") for t in transits[:10]]
    prompt = (
        "Опиши, как использовать энергию ближайших транзитов. Дай 2–3 абзаца с"
        " практическими советами.\n\nТранзиты:\n"
        + "\n".join(f"- {line}" for line in transit_lines)
    )
    return await _ask_llm(prompt, max_tokens=600)


def planet_in_sign_label(planet_name: str, sign: str) -> str:
    """Pure helper so we can also offer offline mini-blurbs in inline mode."""
    ru_name = PLANET_NAMES_RU.get(planet_name, planet_name)
    return f"{ru_name} в знаке {sign}"
