"""
AI-powered astrological interpretations using OpenAI GPT-4.
Falls back to pre-written templates if API is unavailable.
"""
from __future__ import annotations

import json
import random
from typing import Optional
from app.config import settings
from app.astrology.calculations import NatalChart, PLANET_NAMES_RU

try:
    from openai import AsyncOpenAI
    _client: Optional[AsyncOpenAI] = None

    def _get_client() -> Optional[AsyncOpenAI]:
        global _client
        if settings.OPENAI_API_KEY and not _client:
            _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return _client

except ImportError:
    def _get_client():
        return None


SYSTEM_PROMPT = """Ты — профессиональный астролог с 20-летним опытом. Твоя роль — мудрый наставник с доступным языком.

При анализе используй:
- Позиции планет в знаках зодиака и домах
- Основные аспекты (соединения, оппозиции, тригоны, квадраты, секстили)
- Текущие транзиты для прогнозов
- Практические советы, позитивный тон

Правила форматирования:
- Длина ответа: 2-3 абзаца максимум
- Используй эмодзи для живости (⭐, 🌟, ✨, 🌙, ☀️, 💫)
- Заканчивай практическим советом или аффирмацией
- ВСЕГДА добавляй: "⚠️ Астрология носит развлекательный характер."

Язык: русский."""


def _format_chart_for_prompt(chart: NatalChart) -> str:
    lines = [f"Натальная карта:"]
    for name, planet in chart.planets.items():
        if name == "Ascendant":
            continue
        lines.append(f"- {PLANET_NAMES_RU.get(name, name)}: {planet.sign_ru} {int(planet.degree)}°" +
                     (" (ретроградный)" if planet.retrograde else ""))

    if chart.ascendant > 0:
        from app.astrology.calculations import ZODIAC_SIGNS
        asc_sign = ZODIAC_SIGNS[int(chart.ascendant / 30) % 12]
        lines.append(f"- Асцендент: {asc_sign}")

    if chart.aspects:
        lines.append("\nГлавные аспекты:")
        for aspect in chart.aspects[:5]:
            lines.append(f"- {PLANET_NAMES_RU.get(aspect.planet1, aspect.planet1)} {aspect.aspect_name} "
                         f"{PLANET_NAMES_RU.get(aspect.planet2, aspect.planet2)}")

    return "\n".join(lines)


async def get_natal_interpretation(chart: NatalChart, user_name: str) -> str:
    chart_text = _format_chart_for_prompt(chart)
    prompt = f"""Имя пользователя: {user_name}
{chart_text}

Дай детальный анализ натальной карты: характер, таланты, жизненные задачи и сильные стороны."""

    return await _call_ai(prompt)


async def get_daily_forecast(chart: NatalChart, user_name: str, transit_chart: Optional[NatalChart] = None) -> str:
    chart_text = _format_chart_for_prompt(chart)
    transit_text = ""
    if transit_chart:
        transit_text = f"\nТекущие транзиты:\n{_format_chart_for_prompt(transit_chart)}"

    prompt = f"""Имя: {user_name}
{chart_text}{transit_text}

Дай персональный прогноз на сегодня: что важно учесть, на что обратить внимание, благоприятные сферы."""

    return await _call_ai(prompt)


async def get_weekly_forecast(chart: NatalChart, user_name: str) -> str:
    chart_text = _format_chart_for_prompt(chart)
    prompt = f"""Имя: {user_name}
{chart_text}

Дай прогноз на ближайшую неделю: ключевые темы, благоприятные и сложные дни, советы."""

    return await _call_ai(prompt)


async def get_compatibility(chart1: NatalChart, name1: str, chart2: NatalChart, name2: str) -> str:
    text1 = _format_chart_for_prompt(chart1)
    text2 = _format_chart_for_prompt(chart2)
    prompt = f"""Карта {name1}:
{text1}

Карта {name2}:
{text2}

Проанализируй совместимость этих двух людей: эмоциональная связь, общие ценности, сложности и потенциал отношений."""

    return await _call_ai(prompt)


async def get_transit_forecast(chart: NatalChart, user_name: str, transit_chart: NatalChart) -> str:
    chart_text = _format_chart_for_prompt(chart)
    transit_text = _format_chart_for_prompt(transit_chart)
    prompt = f"""Имя: {user_name}
Натальная карта:
{chart_text}

Текущие транзиты:
{transit_text}

Проанализируй важные транзиты и их влияние на жизнь человека в ближайшие недели."""

    return await _call_ai(prompt)


async def answer_question(
    chart: NatalChart,
    user_name: str,
    question: str,
    is_premium: bool = False,
) -> str:
    chart_text = _format_chart_for_prompt(chart)
    depth = "подробный и развёрнутый" if is_premium else "краткий (1-2 абзаца)"
    prompt = f"""Имя: {user_name}
{chart_text}

Вопрос пользователя: {question}

Дай {depth} астрологический ответ на вопрос, основываясь на натальной карте."""

    return await _call_ai(prompt)


async def get_inline_forecast(sign: str) -> str:
    prompt = f"""Дай краткий (3-4 предложения) позитивный прогноз на сегодня для знака {sign}.
Формат: эмодзи + текст. Упомяни ключевые сферы (любовь, работа, здоровье)."""
    return await _call_ai(prompt)


async def get_inline_compatibility(sign1: str, sign2: str) -> str:
    prompt = f"""Дай краткий (3-4 предложения) анализ совместимости {sign1} и {sign2}.
Включи: общий тон отношений, сильные стороны, совет. Добавь эмодзи."""
    return await _call_ai(prompt)


async def _call_ai(prompt: str) -> str:
    client = _get_client()
    if client is None:
        return _get_fallback_response()

    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=800,
            temperature=0.75,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return _get_fallback_response()


def _get_fallback_response() -> str:
    responses = [
        "🌟 Звёзды говорят о важном периоде трансформации. Ваши природные таланты сейчас особенно актуальны — доверяйте своей интуиции и внутреннему голосу.\n\n✨ Сфера отношений требует мягкости и открытости. Карьерные возможности могут появиться неожиданно — будьте готовы действовать решительно.\n\n💫 Совет дня: уделите время медитации или спокойной прогулке на природе. Это поможет восстановить энергетический баланс.\n\n⚠️ Астрология носит развлекательный характер.",
        "☀️ Солнечная энергия усиливает вашу харизму и привлекательность. Сейчас хорошее время для новых начинаний и творческих проектов.\n\n🌙 Луна указывает на важность эмоционального баланса. Прислушайтесь к своим чувствам и потребностям близких людей.\n\n⭐ Практический совет: запишите три цели на неделю и сделайте первый шаг к каждой из них уже сегодня.\n\n⚠️ Астрология носит развлекательный характер.",
        "💫 Меркурий активизирует вашу коммуникативность — это идеальное время для важных переговоров и деловых встреч. Ваши слова будут услышаны.\n\n🌟 Венера привносит гармонию в отношения. Выразите благодарность близким — это укрепит ваши связи.\n\n✨ Аффирмация дня: «Я открыт(а) новым возможностям и с радостью принимаю блага Вселенной».\n\n⚠️ Астрология носит развлекательный характер.",
    ]
    return random.choice(responses)
