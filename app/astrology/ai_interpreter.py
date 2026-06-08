from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from openai import AsyncOpenAI

from app.astrology.calculations import ChartData, calculate_transits
from app.config import DISCLAIMER_TEXT, get_settings


settings = get_settings()


def _fallback_natal(chart: ChartData) -> str:
    headline = chart.summary.replace("Core placements:", "Ваша карта показывает")
    return (
        f"{headline}\n\n"
        "В практическом смысле вам подходят ритм, в котором есть и структура, и место "
        "для интуиции. В ближайшие недели полезно опираться на сильные дома карты и "
        "действовать через небольшие, но последовательные шаги."
    )


def _fallback_daily(chart: ChartData) -> str:
    transits = calculate_transits(chart, datetime.now(UTC))
    if transits:
        first = transits[0]
        return (
            f"Сегодня особенно чувствуется аспект {first['transit_planet']} к вашему "
            f"{first['natal_planet']}. Это день, когда стоит мягко перестроить планы "
            "и дать себе пространство на корректировку курса.\n\n"
            "Лучше всего работают задачи, где важны внимание к деталям, искренний диалог "
            "и бережное отношение к собственному ресурсу."
        )
    return (
        "Сегодня у карты спокойный фон: лучше всего пойдут дела, где нужен баланс между "
        "инициативой и наблюдением. Не перегружайте расписание и оставьте время на "
        "пересборку приоритетов."
    )


def _fallback_compatibility(first_chart: ChartData, second_chart: ChartData, score: int) -> str:
    return (
        f"Синастрия показывает совместимость на уровне {score}/100. Между картами есть "
        "несколько сильных точек притяжения, но их потенциал раскрывается только при "
        "открытом разговоре о границах и ожиданиях.\n\n"
        "Сильнее всего союз растет через честность, уважение к разному темпу и готовность "
        "не спорить за лидерство, а дополнять друг друга."
    )


def _fallback_question(chart: ChartData, question: str) -> str:
    return (
        f"Если смотреть на ваш вопрос через призму натальной карты, главный вектор сейчас — "
        f"не форсировать решение, а выстроить ясную внутреннюю опору. Вопрос: “{question}”.\n\n"
        "Сначала определите, что находится в вашей зоне контроля, а затем выберите один "
        "практический шаг на ближайшие сутки. Это даст больше пользы, чем попытка решить "
        "все сразу."
    )


async def _openai_completion(prompt: str) -> str:
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.responses.create(
        model=settings.openai_model,
        input=[
            {
                "role": "system",
                "content": (
                    "Ты — профессиональный астролог с 20-летним опытом. "
                    "Анализируй карты по планетам, домам, аспектам и транзитам. "
                    "Тон — теплый и поддерживающий, язык — простой, ответ 2-3 абзаца. "
                    "Не давай медицинских, финансовых или юридических советов и "
                    "всегда соблюдай развлекательный характер сервиса."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
    )
    return response.output_text.strip()


async def interpret_natal_chart(chart: ChartData) -> str:
    if not settings.openai_api_key:
        return _fallback_natal(chart)

    prompt = (
        "Сделай интерпретацию натальной карты.\n"
        f"Данные: {chart.as_dict()}\n"
        f"Добавь краткий дисклеймер сервиса: {DISCLAIMER_TEXT}"
    )
    return await _openai_completion(prompt)


async def interpret_daily_forecast(chart: ChartData) -> str:
    if not settings.openai_api_key:
        return _fallback_daily(chart)

    prompt = (
        "Сделай персональный прогноз на сегодня по натальной карте и транзитам.\n"
        f"Карта: {chart.as_dict()}\n"
        f"Транзиты: {calculate_transits(chart)}"
    )
    return await _openai_completion(prompt)


async def interpret_weekly_forecast(chart: ChartData) -> str:
    if not settings.openai_api_key:
        return (
            "Неделя выглядит как этап перенастройки фокуса. Сначала лучше завершать "
            "незакрытые дела, а уже потом входить в новые обязательства.\n\n"
            "Особенно полезны будут планирование, разговоры о целях и отказ от всего, "
            "что съедает энергию без заметного результата."
        )

    prompt = (
        "Сделай прогноз на 7 дней по натальной карте и текущим транзитам.\n"
        f"Карта: {chart.as_dict()}\n"
        f"Транзиты: {calculate_transits(chart)}"
    )
    return await _openai_completion(prompt)


async def interpret_transits(chart: ChartData) -> str:
    transits = calculate_transits(chart)
    if not settings.openai_api_key:
        if not transits:
            return "Сейчас карта не показывает напряженных транзитов: это хорошее окно для спокойной настройки целей."
        lines = [
            f"• {item['transit_planet']} {item['aspect']} {item['natal_planet']} (orb {item['orb']})"
            for item in transits[:5]
        ]
        return "Ближайшие важные транзиты:\n" + "\n".join(lines)

    prompt = (
        "Опиши главные текущие транзиты и что они значат на практике.\n"
        f"Карта: {chart.as_dict()}\n"
        f"Транзиты: {transits}"
    )
    return await _openai_completion(prompt)


async def interpret_compatibility(
    first_chart: ChartData,
    second_chart: ChartData,
    compatibility: dict[str, Any],
) -> str:
    if not settings.openai_api_key:
        return _fallback_compatibility(first_chart, second_chart, int(compatibility["score"]))

    prompt = (
        "Сделай анализ совместимости (синастрию) для двух карт.\n"
        f"Первая карта: {first_chart.as_dict()}\n"
        f"Вторая карта: {second_chart.as_dict()}\n"
        f"Итоговые метрики: {compatibility}"
    )
    return await _openai_completion(prompt)


async def answer_personal_question(chart: ChartData, question: str) -> str:
    if not settings.openai_api_key:
        return _fallback_question(chart, question)

    prompt = (
        "Ответь на личный вопрос пользователя на основе натальной карты и текущих транзитов.\n"
        f"Карта: {chart.as_dict()}\n"
        f"Вопрос: {question}\n"
        f"Транзиты: {calculate_transits(chart)}"
    )
    return await _openai_completion(prompt)
