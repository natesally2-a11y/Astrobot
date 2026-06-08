"""OpenAI GPT-based astrology interpreter.

When ``OPENAI_API_KEY`` is missing we degrade gracefully by returning a
heuristic textual fallback so the bot remains usable in development.
"""
from __future__ import annotations

import asyncio
from typing import Optional

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except Exception:  # pragma: no cover
    AsyncOpenAI = None  # type: ignore
    OPENAI_AVAILABLE = False

from loguru import logger

from app.astrology.calculations import NatalChart, format_planet_line, summary
from app.config import get_settings


SYSTEM_PROMPT = """Ты — профессиональный астролог с 20-летним опытом.
Анализируй натальную карту, используя:
- Позиции планет в знаках и домах
- Основные аспекты (соединения, оппозиции, тригоны, квадраты)
- Текущие транзиты для прогнозов
- Стиль: мудрый наставник, но доступный язык
- Длина ответа: 2-3 абзаца максимум
- Фокус на практических советах и позитивном тоне
- Всегда добавляй в конце короткое напоминание, что прогноз носит
  развлекательный характер (1 строкой).
- Отвечай на русском языке.
"""


def _client() -> Optional["AsyncOpenAI"]:
    settings = get_settings()
    if not settings.openai_api_key or not OPENAI_AVAILABLE:
        return None
    return AsyncOpenAI(api_key=settings.openai_api_key)


def _format_chart_context(chart: NatalChart, label: str = "Натальная карта") -> str:
    lines = [f"{label}:"]
    for p in chart.planets.values():
        lines.append("• " + format_planet_line(p))
    if chart.ascendant is not None:
        lines.append(f"• ASC: {chart.ascendant:.1f}°")
    if chart.midheaven is not None:
        lines.append(f"• MC: {chart.midheaven:.1f}°")
    if chart.aspects:
        lines.append("Аспекты:")
        for asp in chart.aspects[:10]:
            a = chart.planets[asp.planet_a]
            b = chart.planets[asp.planet_b]
            lines.append(
                f"• {a.name_ru} {asp.name_ru} {b.name_ru} (орб {asp.orb:.1f}°)"
            )
    return "\n".join(lines)


async def _chat(messages: list[dict], temperature: float = 0.85, max_tokens: int = 600) -> str:
    settings = get_settings()
    client = _client()
    if client is None:
        return ""
    try:
        resp = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as exc:  # pragma: no cover
        logger.exception("OpenAI request failed: {}", exc)
        return ""


# --- Public helpers -------------------------------------------------------

async def interpret_natal_chart(chart: NatalChart, *, name: Optional[str] = None) -> str:
    intro = f"Имя: {name}\n\n" if name else ""
    context = _format_chart_context(chart)
    user_prompt = (
        f"{intro}{context}\n\n"
        "Сделай развернутую характеристику личности на основе этой карты: "
        "ключевые таланты, темы жизни, точки роста. 2-3 абзаца, тёплый "
        "поддерживающий тон."
    )
    text = await _chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
    )
    if text:
        return text
    return _fallback_natal(chart)


async def daily_forecast(
    chart: NatalChart, transit_chart: NatalChart, *, name: Optional[str] = None
) -> str:
    intro = f"Имя: {name}\n\n" if name else ""
    user_prompt = (
        f"{intro}"
        f"{_format_chart_context(chart, 'Натальная карта')}\n\n"
        f"{_format_chart_context(transit_chart, 'Транзиты на сегодня')}\n\n"
        "Опиши, что несёт сегодняшний день: главное настроение, на что обратить "
        "внимание, чего избегать, какой практический совет можно дать. "
        "2 абзаца, мудрый дружеский тон."
    )
    text = await _chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=450,
    )
    if text:
        return text
    return _fallback_daily(chart, transit_chart)


async def weekly_forecast(
    chart: NatalChart, transit_chart: NatalChart, *, name: Optional[str] = None
) -> str:
    intro = f"Имя: {name}\n\n" if name else ""
    user_prompt = (
        f"{intro}"
        f"{_format_chart_context(chart, 'Натальная карта')}\n\n"
        f"{_format_chart_context(transit_chart, 'Транзиты на эту неделю')}\n\n"
        "Дай прогноз на ближайшие 7 дней: ключевые темы недели, благоприятные "
        "и непростые дни, рекомендации. 3 абзаца."
    )
    text = await _chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=700,
    )
    if text:
        return text
    return _fallback_weekly(chart)


async def compatibility(
    chart_a: NatalChart, chart_b: NatalChart,
    *, score: int, highlights: list[str],
    name_a: Optional[str] = None, name_b: Optional[str] = None,
) -> str:
    a_label = f"Карта 1{f' ({name_a})' if name_a else ''}"
    b_label = f"Карта 2{f' ({name_b})' if name_b else ''}"
    highlight_block = "\n".join(f"• {h}" for h in highlights) or "—"
    user_prompt = (
        f"{_format_chart_context(chart_a, a_label)}\n\n"
        f"{_format_chart_context(chart_b, b_label)}\n\n"
        f"Индекс совместимости: {score}/100.\n"
        f"Ключевые аспекты синастрии:\n{highlight_block}\n\n"
        "Расскажи о совместимости этих двух людей: сильные стороны союза, "
        "сложности, рекомендации. 3 абзаца, без оценочных суждений."
    )
    text = await _chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=650,
    )
    if text:
        return text
    return _fallback_compat(score, highlights)


async def transit_brief(chart: NatalChart, transit_chart: NatalChart) -> str:
    user_prompt = (
        f"{_format_chart_context(chart, 'Натальная карта')}\n\n"
        f"{_format_chart_context(transit_chart, 'Транзиты на сегодня')}\n\n"
        "Перечисли 3-5 самых важных транзитов и кратко объясни их влияние. "
        "Используй маркированный список."
    )
    text = await _chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
    )
    if text:
        return text
    return _fallback_transits(transit_chart)


async def answer_question(chart: NatalChart, question: str) -> str:
    context = _format_chart_context(chart)
    user_prompt = (
        f"{context}\n\nВопрос пользователя: {question}\n\n"
        "Ответь, опираясь на натальную карту. 2 абзаца, без эзотерических клише."
    )
    text = await _chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
    )
    if text:
        return text
    return _fallback_question(chart, question)


# --- Fallback heuristics --------------------------------------------------

def _fallback_natal(chart: NatalChart) -> str:
    sun = chart.planets.get("Sun")
    moon = chart.planets.get("Moon")
    asc = chart.ascendant_sign_ru()
    parts = [
        "🌟 Ваша натальная карта",
        "",
        f"Солнце в знаке {sun.sign_ru if sun else '—'} — это ваше «я», стиль "
        f"проявления и источник энергии.",
        f"Луна в {moon.sign_ru if moon else '—'} рассказывает об эмоциях, привычках, "
        "способах заботы о себе.",
        f"Асцендент в {asc} формирует первое впечатление, которое вы производите.",
        "",
        summary(chart),
        "",
        "⚠️ Анализ носит развлекательный характер.",
    ]
    return "\n".join(parts)


def _fallback_daily(chart: NatalChart, transit_chart: NatalChart) -> str:
    moon = transit_chart.planets.get("Moon")
    sun = transit_chart.planets.get("Sun")
    parts = [
        "✨ Прогноз на сегодня",
        "",
        f"Сегодня Луна в {moon.sign_ru if moon else '—'} — обратите внимание на "
        f"настроение и интуитивные сигналы.",
        f"Солнце в {sun.sign_ru if sun else '—'} задаёт общий тон дня: "
        "посвятите время важным для вас целям.",
        "",
        "⚠️ Прогноз носит развлекательный характер.",
    ]
    return "\n".join(parts)


def _fallback_weekly(chart: NatalChart) -> str:
    return (
        "📅 Прогноз на неделю\n\n"
        "Эта неделя — хорошее время сосредоточиться на ваших ключевых темах: "
        f"Солнце в {chart.sun_sign_ru()} подсказывает направление, "
        f"Луна в {chart.moon_sign_ru()} напоминает о заботе о себе.\n\n"
        "⚠️ Прогноз носит развлекательный характер."
    )


def _fallback_compat(score: int, highlights: list[str]) -> str:
    body = "\n".join(f"• {h}" for h in highlights) or "—"
    return (
        f"💞 Совместимость: {score}/100\n\n"
        "Ключевые аспекты синастрии:\n" + body +
        "\n\n⚠️ Анализ носит развлекательный характер."
    )


def _fallback_transits(transit_chart: NatalChart) -> str:
    lines = ["🪐 Транзиты на сегодня:"]
    for p in transit_chart.planets.values():
        lines.append("• " + format_planet_line(p))
    lines.append("\n⚠️ Прогноз носит развлекательный характер.")
    return "\n".join(lines)


def _fallback_question(chart: NatalChart, question: str) -> str:
    return (
        f"Вы спрашиваете: {question}\n\n"
        "Сейчас ИИ-астролог недоступен (не настроен ключ OpenAI), но ваша карта "
        f"подсказывает: Солнце в {chart.sun_sign_ru()}, Луна в {chart.moon_sign_ru()}. "
        "Прислушайтесь к этим архетипам, формулируя ответ.\n\n"
        "⚠️ Ответ носит развлекательный характер."
    )


# Synchronous shim — handy for tests / debug.
def interpret_natal_chart_sync(chart: NatalChart, *, name: Optional[str] = None) -> str:
    return asyncio.run(interpret_natal_chart(chart, name=name))
