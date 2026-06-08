from __future__ import annotations

import json
from datetime import date

from openai import AsyncOpenAI

from app.astrology.calculations import Aspect, ChartData
from app.config import get_settings

settings = get_settings()

SYSTEM_PROMPT = """Ты профессиональный астролог с 20-летним опытом.
Анализируй натальную карту и транзиты, используя:
- позиции планет в знаках и домах
- ключевые аспекты
- текущие транзиты для прогнозов

Стиль:
- мудрый наставник, но доступный и теплый язык
- 2-3 абзаца максимум
- фокус на практических советах и позитивном тоне

Всегда добавляй мягкий дисклеймер, что прогноз носит развлекательный характер.
"""


def _format_chart(chart: ChartData) -> str:
    payload = {
        "place": chart.place,
        "date": chart.date,
        "time": chart.time,
        "ascendant": chart.ascendant,
        "planets": [
            {
                "name": p.name,
                "sign": p.sign,
                "house": p.house,
                "degree": round(p.degree_in_sign, 2),
            }
            for p in chart.planets
        ],
        "aspects": [
            {
                "between": f"{a.planet_a}-{a.planet_b}",
                "type": a.aspect_type,
                "orb": a.orb,
            }
            for a in chart.aspects[:20]
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def _format_transits(transits: list[Aspect]) -> str:
    return json.dumps(
        [
            {
                "between": f"{t.planet_a}-{t.planet_b}",
                "type": t.aspect_type,
                "orb": t.orb,
            }
            for t in transits[:20]
        ],
        ensure_ascii=False,
    )


async def _ask_openai(user_prompt: str) -> str | None:
    if not settings.openai_api_key:
        return None
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.responses.create(
        model=settings.openai_model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_output_tokens=500,
    )
    return (response.output_text or "").strip()


async def natal_interpretation(chart: ChartData, user_name: str | None) -> str:
    user_prompt = (
        f"Сделай персональный разбор натальной карты для пользователя {user_name or 'пользователь'}.\n"
        f"Данные карты: {_format_chart(chart)}"
    )
    ai = await _ask_openai(user_prompt)
    if ai:
        return ai

    top_planets = ", ".join(f"{p.name} в {p.sign}" for p in chart.planets[:4])
    return (
        f"В вашей карте особенно заметны: {top_planets}. Это сочетание говорит о сильной личной инициативе, "
        "умении адаптироваться и потенциале к устойчивому росту через осознанные решения.\n\n"
        "На практике важно опираться на ритм дня, фиксировать цели письменно и распределять нагрузку по приоритетам. "
        "Так вы быстрее увидите результат и снизите эмоциональные перегрузки.\n\n"
        "Прогноз носит развлекательный характер и подходит для саморазвития."
    )


async def daily_interpretation(chart: ChartData, transits: list[Aspect], target_date: date) -> str:
    user_prompt = (
        f"Сформируй персональный прогноз на {target_date.isoformat()}.\n"
        f"Натальная карта: {_format_chart(chart)}\n"
        f"Транзиты: {_format_transits(transits)}"
    )
    ai = await _ask_openai(user_prompt)
    if ai:
        return ai
    transit_preview = ", ".join(f"{t.planet_a} {t.aspect_type} {t.planet_b}" for t in transits[:3])
    return (
        f"Сегодня ключевые влияния дня: {transit_preview or 'плавный фон без резких аспектов'}. "
        "Лучше действовать последовательно, без перегруза, и оставлять время на восстановление.\n\n"
        "Хорошо заходят задачи, где нужна концентрация, а в общении важно заранее формулировать ожидания. "
        "Это поможет избежать лишних конфликтов и укрепить поддержку вокруг.\n\n"
        "Это развлекательный астрологический прогноз, не заменяющий профессиональные рекомендации."
    )


async def compatibility_interpretation(
    first_chart: ChartData,
    second_chart: ChartData,
    score: int,
    highlights: list[str],
) -> str:
    user_prompt = (
        "Сделай краткий разбор совместимости двух людей.\n"
        f"Карта 1: {_format_chart(first_chart)}\n"
        f"Карта 2: {_format_chart(second_chart)}\n"
        f"Оценка совместимости: {score}/99; акценты: {json.dumps(highlights, ensure_ascii=False)}"
    )
    ai = await _ask_openai(user_prompt)
    if ai:
        return ai

    hints = "; ".join(highlights) if highlights else "мягкая, нейтральная синхронизация"
    return (
        f"Итоговая совместимость: {score}/99. Главные акценты: {hints}.\n\n"
        "Пара может усиливать друг друга через честный диалог и ясное распределение ожиданий. "
        "Чем больше прозрачности в бытовых и эмоциональных вопросах, тем стабильнее союз.\n\n"
        "Интерпретация носит развлекательный характер."
    )


async def answer_astrology_question(chart: ChartData, question: str) -> str:
    user_prompt = (
        "Ответь на вопрос пользователя, учитывая его карту и практический тон.\n"
        f"Карта: {_format_chart(chart)}\n"
        f"Вопрос: {question}"
    )
    ai = await _ask_openai(user_prompt)
    if ai:
        return ai

    return (
        "Судя по вашей карте, сейчас лучше опираться на небольшие, но регулярные шаги и не пытаться решить всё сразу. "
        "Вопрос, который вы задали, лучше прояснять через конкретный план на 1-2 недели и наблюдение за реакцией окружения.\n\n"
        "Если хотите, я могу разбить ваш запрос на три практических действия на ближайшие дни.\n\n"
        "Напоминание: астрология здесь используется как инструмент самоанализа и развлечения."
    )
