from app.astrology.calculations import NatalChart, important_transits, summarize_chart
from app.config import Settings, get_settings

SYSTEM_PROMPT = """Ты — профессиональный астролог с 20-летним опытом.
Анализируй натальную карту, используя:
- Позиции планет в знаках и домах
- Основные аспекты: соединения, оппозиции, тригоны, квадраты и секстили
- Текущие транзиты для прогнозов
- Стиль: мудрый наставник, но доступный язык
- Длина ответа: 2-3 абзаца максимум
- Фокус на практических советах и позитивном тоне

Всегда добавляй мягкое напоминание, что астрология носит развлекательный характер."""


class AstrologyInterpreter:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def natal_reading(self, chart: NatalChart) -> str:
        prompt = (
            "Сделай персональный базовый анализ натальной карты. "
            f"Место рождения: {chart.birth_place}. {summarize_chart(chart)}"
        )
        return await self._complete(prompt, fallback=_fallback_natal(chart))

    async def daily_forecast(self, chart: NatalChart, detailed: bool = False) -> str:
        transits = important_transits(chart)
        prompt = (
            "Сделай персональный прогноз на сегодня по натальной карте и текущим транзитам. "
            f"Детализация: {'подробно' if detailed else 'кратко'}. "
            f"Натальная карта: {summarize_chart(chart)}. Транзиты: {'; '.join(transits) or 'нет точных транзитов'}."
        )
        return await self._complete(prompt, fallback=_fallback_daily(chart, transits, detailed))

    async def weekly_forecast(self, chart: NatalChart) -> str:
        prompt = (
            "Сделай прогноз на неделю для premium-пользователя. "
            f"Используй карту: {summarize_chart(chart)}."
        )
        return await self._complete(prompt, fallback=_fallback_period("неделя", chart))

    async def transit_forecast(self, chart: NatalChart) -> str:
        transits = important_transits(chart)
        prompt = (
            "Объясни важные текущие транзиты и практические рекомендации. "
            f"Натальная карта: {summarize_chart(chart)}. Транзиты: {'; '.join(transits) or 'нет точных транзитов'}."
        )
        return await self._complete(prompt, fallback=_fallback_transits(transits))

    async def answer_question(self, chart: NatalChart, question: str) -> str:
        prompt = (
            "Ответь на вопрос пользователя с опорой на карту, без медицинских, финансовых или юридических директив. "
            f"Вопрос: {question}. Карта: {summarize_chart(chart)}."
        )
        return await self._complete(prompt, fallback=_fallback_question(question, chart))

    async def compatibility(self, user_chart: NatalChart, partner_chart: NatalChart) -> str:
        prompt = (
            "Сделай краткий анализ совместимости двух натальных карт: сильные стороны, зоны роста, совет. "
            f"Карта пользователя: {summarize_chart(user_chart)}. "
            f"Карта партнера: {summarize_chart(partner_chart)}."
        )
        return await self._complete(prompt, fallback=_fallback_compatibility(user_chart, partner_chart))

    async def _complete(self, prompt: str, fallback: str) -> str:
        if self.settings.openai_api_key is None:
            return fallback

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.settings.require_openai_key())
            response = await client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=700,
            )
            content = response.choices[0].message.content
            return content.strip() if content else fallback
        except Exception:
            return fallback


def _fallback_natal(chart: NatalChart) -> str:
    sun = _planet(chart, "Sun")
    moon = _planet(chart, "Moon")
    asc_house = f", акцент {sun.house} дома" if sun and sun.house else ""
    return (
        f"Ваша карта подчеркивает сочетание Солнца в {sun.sign if sun else 'личном знаке'}"
        f"{asc_house} и Луны в {moon.sign if moon else 'эмоциональной зоне'}. Это дает сильный потенциал "
        "самопознания: важно соединять внешние цели с внутренним ощущением безопасности.\n\n"
        "Практический совет: сегодня выберите одну тему, где вы хотите больше ясности, и запишите три честных "
        "наблюдения о себе. Астрология здесь служит инструментом размышления и развлечения, а не инструкцией к действию."
    )


def _fallback_daily(chart: NatalChart, transits: list[str], detailed: bool) -> str:
    emphasis = transits[0] if transits else "день подходит для спокойной настройки на свои приоритеты"
    detail = (
        "Добавьте к планам больше пространства для отдыха и честного разговора с собой. "
        if detailed
        else ""
    )
    return (
        f"Сегодня главный акцент: {emphasis}. Ваша карта советует действовать мягко, но последовательно: "
        f"выберите один важный шаг и доведите его до конца. {detail}\n\n"
        "Прогноз носит развлекательный характер и помогает посмотреть на день под новым углом."
    )


def _fallback_period(period: str, chart: NatalChart) -> str:
    sun = _planet(chart, "Sun")
    return (
        f"На период «{period}» карта с Солнцем в {sun.sign if sun else 'вашем знаке'} предлагает сфокусироваться "
        "на устойчивом ритме: меньше распыляться, больше завершать начатое.\n\n"
        "Лучшие результаты придут через маленькие регулярные действия. Используйте прогноз как творческую подсказку, "
        "а важные решения принимайте с опорой на факты и специалистов."
    )


def _fallback_transits(transits: list[str]) -> str:
    if not transits:
        return (
            "Сейчас нет особо точных мажорных транзитов к вашей карте, поэтому период можно использовать для "
            "спокойной стабилизации и восстановления.\n\nАстрологическая информация носит развлекательный характер."
        )
    return (
        "Важные транзиты: " + "; ".join(transits[:4]) + ". Эти темы могут подсветить внутреннюю динамику дня, "
        "особенно в вопросах выбора, общения и личных границ.\n\nИспользуйте это как повод для саморефлексии."
    )


def _fallback_question(question: str, chart: NatalChart) -> str:
    moon = _planet(chart, "Moon")
    return (
        f"Ваш вопрос: «{question}». Луна в {moon.sign if moon else 'карте'} показывает, что сначала стоит "
        "проверить эмоциональную мотивацию: чего вы на самом деле хотите и где ищете подтверждения извне?\n\n"
        "Сформулируйте самый бережный следующий шаг. Ответ является развлекательной астрологической интерпретацией."
    )


def _fallback_compatibility(user_chart: NatalChart, partner_chart: NatalChart) -> str:
    user_sun = _planet(user_chart, "Sun")
    partner_sun = _planet(partner_chart, "Sun")
    return (
        f"Связка Солнца в {user_sun.sign if user_sun else 'вашей карте'} и "
        f"{partner_sun.sign if partner_sun else 'карте партнера'} может дать интересный обмен энергией: "
        "один партнер помогает проявляться, другой подсвечивает новые способы реагировать.\n\n"
        "Зона роста — говорить о ожиданиях прямо и не пытаться угадывать чувства друг друга. Это развлекательная "
        "синастрическая интерпретация, а не прогноз судьбы отношений."
    )


def _planet(chart: NatalChart, key: str):
    return next((planet for planet in chart.planets if planet.key == key), None)
