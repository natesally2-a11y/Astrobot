from __future__ import annotations

import json

from openai import AsyncOpenAI

from app.astrology.calculations import summarize_chart
from app.config import settings

SYSTEM_PROMPT = '''Ты — профессиональный астролог с 20-летним опытом.
Анализируй натальную карту, используя позиции планет в знаках и домах,
основные аспекты и текущие транзиты. Стиль — мудрый наставник,
но с понятным современным языком. Ответ держи в 2-3 абзацах,
фокус на практических советах, позитивном тоне и персонализации.'''


def _fallback_natal(chart: dict, first_name: str | None) -> str:
    name = first_name or 'друг'
    planets = {planet['name']: planet for planet in chart['planets']}
    sun = planets['Sun']
    moon = planets['Moon']
    major = chart['aspects'][:3]
    aspect_text = ', '.join(f"{item['between'][0]}-{item['between'][1]} {item['aspect'].lower()}" for item in major) or 'акцент на мягкой внутренней перестройке'
    return (
        f"{name}, в твоей карте Солнце в {sun['sign']} и Луна в {moon['sign']}, поэтому ты сочетаешь яркую самопрезентацию с глубокой эмоциональной интуицией. Дом Солнца ({sun['house']}) показывает, где особенно важно проявляться смело и последовательно.\n\n"
        f"Сейчас карта подсказывает делать ставку на сильные стороны, а не на самокритику. Важные аспекты ({aspect_text}) говорят, что рост приходит через баланс между чувствами и действием. Полезно фиксировать идеи и выбирать конкретные маленькие шаги вместо резких решений."
    )


def _fallback_daily(chart: dict, transits: dict, first_name: str | None) -> str:
    name = first_name or 'друг'
    highlights = transits['important_transits'][:3]
    if highlights:
        fragments = ', '.join(f"{item['transit_planet']} {item['aspect'].lower()} к твоему Солнцу" for item in highlights)
    else:
        fragments = 'сегодняшний день проходит без жестких напряженных аспектов'
    return (
        f"{name}, по текущим транзитам {fragments}. Это хороший момент, чтобы действовать спокойно и опираться на свой естественный ритм.\n\n"
        'Фокус дня — на том, что можно улучшить уже сейчас: короткие разговоры, аккуратное планирование и бережное отношение к энергии. Не спеши принимать большие решения только на эмоциях.'
    )


def _fallback_compatibility(report: dict, partner_name: str) -> str:
    aspect_text = ', '.join(f"{item['between'][0]} / {item['between'][1]} — {item['aspect']}" for item in report['aspects'][:4])
    return (
        f"Совместимость с {partner_name} оценивается на {report['score']} из 99. Между вами есть сильный эмоционально-химический потенциал, особенно если вы умеете проговаривать ожидания и не уходить в молчаливые обиды.\n\n"
        f"Ключевые аспекты: {aspect_text or 'гармоничные точки контакта преобладают'}. Лучший сценарий для пары — развивать ясность в договоренностях и оставлять пространство для индивидуальности каждого."
    )


async def _generate(messages: list[dict[str, str]]) -> str | None:
    if not settings.openai_api_key:
        return None
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    try:
        response = await client.responses.create(model=settings.openai_model, input=messages)
    except Exception:
        return None
    return getattr(response, 'output_text', None)


async def generate_natal_reading(chart: dict, first_name: str | None = None) -> str:
    fallback = _fallback_natal(chart, first_name)
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': f"Имя: {first_name or 'не указано'}\nДанные карты: {json.dumps(chart, ensure_ascii=False)}"},
    ]
    return (await _generate(messages)) or fallback


async def generate_daily_reading(chart: dict, transits: dict, first_name: str | None = None) -> str:
    fallback = _fallback_daily(chart, transits, first_name)
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': f"Имя: {first_name or 'не указано'}\nКраткое описание карты: {summarize_chart(chart)}\nТранзиты: {json.dumps(transits, ensure_ascii=False)}"},
    ]
    return (await _generate(messages)) or fallback


async def generate_weekly_reading(chart: dict, transits: dict, first_name: str | None = None) -> str:
    daily = await generate_daily_reading(chart, transits, first_name)
    return daily + '\n\nНа ближайшие дни стоит сохранять гибкость в расписании, отслеживать энергетические пики и не забывать о восстановлении.'


async def generate_question_reading(chart: dict, question: str, first_name: str | None = None) -> str:
    fallback = (
        f"{first_name or 'друг'}, твой вопрос звучит так: \"{question}\". Карта советует не искать один магический ответ, а посмотреть, где ты можешь вернуть себе инициативу и ясность.\n\n"
        'Сфокусируйся на действиях, которые можно сделать в ближайшие 24 часа, и прислушайся к тому, что повторяется в общении и внутреннем состоянии.'
    )
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': f"Карта: {json.dumps(chart, ensure_ascii=False)}\nВопрос: {question}"},
    ]
    return (await _generate(messages)) or fallback


async def generate_compatibility_reading(report: dict, partner_name: str) -> str:
    fallback = _fallback_compatibility(report, partner_name)
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': f"Синастрия с {partner_name}: {json.dumps(report, ensure_ascii=False)}"},
    ]
    return (await _generate(messages)) or fallback
