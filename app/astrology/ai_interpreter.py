"""AI-powered astrological interpretation using OpenAI."""

from openai import AsyncOpenAI

from app.config import settings
from app.astrology.calculations import (
    NatalChart,
    PlanetPosition,
    Aspect,
    format_chart_text,
    format_transits_text,
    get_current_transits,
    calculate_transit_aspects,
)

client: AsyncOpenAI | None = None


def get_openai_client() -> AsyncOpenAI:
    global client
    if client is None:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
    return client


SYSTEM_PROMPT = """Ты — профессиональный астролог с 20-летним опытом по имени Stellarium AI.

Правила работы:
- Анализируй натальную карту, используя позиции планет в знаках и домах
- Учитывай основные аспекты (соединения, оппозиции, тригоны, квадраты, секстили)
- Для прогнозов используй текущие транзиты относительно натальной карты
- Стиль: мудрый наставник, но доступный язык, без лишнего пафоса
- Длина ответа: 2-3 абзаца максимум (если не просят подробнее)
- Фокус на практических советах и позитивном тоне
- Отвечай на русском языке
- Используй астрологическую терминологию, но объясняй простым языком
- НЕ говори что ты ИИ или программа — ты астролог
- В конце каждого чтения добавь дисклеймер мелким текстом

Дисклеймер (добавляй в конце):
_⚠️ Прогноз носит развлекательный характер._"""


async def interpret_natal_chart(chart: NatalChart, user_name: str = "") -> str:
    """Generate AI interpretation of a natal chart."""
    chart_text = format_chart_text(chart)

    prompt = f"""Проанализируй натальную карту{f' для {user_name}' if user_name else ''}.

{chart_text}

Дай краткий, но содержательный анализ личности: основные черты характера, таланты и области для развития. 
Обрати внимание на ключевые конфигурации (большой крест, большой тригон и т.д., если есть).
Используй эмодзи для визуального оформления."""

    return await _call_ai(prompt)


async def interpret_daily_forecast(
    chart: NatalChart, user_name: str = "", detailed: bool = False
) -> str:
    """Generate personalized daily forecast based on transits."""
    chart_text = format_chart_text(chart)
    transits = get_current_transits()
    transit_aspects = calculate_transit_aspects(chart.planets, transits)
    transits_text = format_transits_text(chart, transits, transit_aspects)

    detail_instruction = (
        "Дай подробный прогноз на день с разбором каждого активного транзита."
        if detailed
        else "Дай краткий прогноз на сегодня — 2-3 абзаца с главными тенденциями."
    )

    prompt = f"""Составь персональный прогноз на сегодня{f' для {user_name}' if user_name else ''}.

Натальная карта:
{chart_text}

{transits_text}

{detail_instruction}
Фокус на практических советах: что делать, чего избегать, на что обратить внимание."""

    return await _call_ai(prompt)


async def interpret_weekly_forecast(chart: NatalChart, user_name: str = "") -> str:
    """Generate personalized weekly forecast."""
    chart_text = format_chart_text(chart)
    transits = get_current_transits()
    transit_aspects = calculate_transit_aspects(chart.planets, transits, orb=5.0)
    transits_text = format_transits_text(chart, transits, transit_aspects)

    prompt = f"""Составь персональный прогноз на неделю{f' для {user_name}' if user_name else ''}.

Натальная карта:
{chart_text}

{transits_text}

Раздели прогноз по дням или тематическим блокам (любовь, карьера, здоровье).
Укажи наиболее благоприятные и сложные дни."""

    return await _call_ai(prompt)


async def interpret_compatibility(
    chart1: NatalChart,
    chart2: NatalChart,
    name1: str = "Партнер 1",
    name2: str = "Партнер 2",
) -> str:
    """Generate synastry / compatibility reading."""
    chart1_text = format_chart_text(chart1)
    chart2_text = format_chart_text(chart2)

    cross_aspects = calculate_transit_aspects(chart1.planets, chart2.planets, orb=5.0)
    aspects_text = "\n".join(
        f"  {a.planet1} — {a.planet2}: {a.aspect_type} (орб {a.orb:.1f}°)"
        for a in cross_aspects[:15]
    )

    prompt = f"""Проанализируй совместимость двух людей.

{name1}:
{chart1_text}

{name2}:
{chart2_text}

Межкарточные аспекты (синастрия):
{aspects_text}

Оцени совместимость по шкале от 1 до 10. 
Разбери: эмоциональную связь, интеллектуальную совместимость, страсть, долгосрочный потенциал.
Укажи сильные стороны союза и возможные трудности."""

    return await _call_ai(prompt)


async def ask_astrologer(
    question: str,
    chart: NatalChart | None = None,
    user_name: str = "",
) -> str:
    """Answer a freeform astrology question."""
    context = ""
    if chart:
        context = f"\nНатальная карта{f' {user_name}' if user_name else ''}:\n{format_chart_text(chart)}\n"

        transits = get_current_transits()
        transit_aspects = calculate_transit_aspects(chart.planets, transits)
        if transit_aspects:
            context += f"\nАктивные транзиты:\n"
            for a in transit_aspects[:5]:
                context += f"  {a.planet1} → {a.planet2}: {a.aspect_type}\n"

    prompt = f"""Пользователь{f' {user_name}' if user_name else ''} задаёт вопрос астрологу:

"{question}"
{context}
Ответь как опытный астролог, опираясь на натальную карту и текущие транзиты (если доступны).
Если вопрос не связан с астрологией, мягко верни разговор к астрологической теме."""

    return await _call_ai(prompt)


async def interpret_transits(chart: NatalChart, user_name: str = "") -> str:
    """Detailed transit analysis."""
    chart_text = format_chart_text(chart)
    transits = get_current_transits()
    transit_aspects = calculate_transit_aspects(chart.planets, transits, orb=5.0)
    transits_text = format_transits_text(chart, transits, transit_aspects)

    prompt = f"""Подробный анализ текущих транзитов{f' для {user_name}' if user_name else ''}.

{chart_text}

{transits_text}

Разбери каждый значимый транзит:
- Что он означает
- Как долго будет действовать
- Практические рекомендации
Выдели самый важный транзит текущего периода."""

    return await _call_ai(prompt)


async def get_inline_compatibility(sign1: str, sign2: str) -> str:
    """Quick compatibility for inline mode (no natal chart needed)."""
    prompt = f"""Кратко опиши совместимость знаков {sign1} и {sign2}.
Формат: одно предложение с эмодзи и оценкой совместимости (1-10).
Пример: "🔥 Лев + Овен (9/10): Огненный и страстный союз двух лидеров!"
"""
    return await _call_ai(prompt, max_tokens=150)


async def get_inline_daily(sign: str) -> str:
    """Quick daily forecast for inline mode."""
    prompt = f"""Дай очень краткий прогноз на сегодня для знака {sign}.
Формат: 2-3 предложения с эмодзи. Фокус на одном главном совете дня.
"""
    return await _call_ai(prompt, max_tokens=200)


async def _call_ai(prompt: str, max_tokens: int = 1000) -> str:
    """Call OpenAI API."""
    ai = get_openai_client()
    try:
        response = await ai.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.8,
        )
        return response.choices[0].message.content or "Не удалось получить ответ."
    except Exception as e:
        return f"⚠️ Звёзды сейчас недоступны. Попробуйте позже.\n\n_Ошибка: {type(e).__name__}_"
