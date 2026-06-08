from openai import AsyncOpenAI

from app.astrology.calculations import ChartCalculator, NatalChart
from app.config import get_settings

SYSTEM_PROMPT = """Ты — профессиональный астролог с 20-летним опытом. Анализируй натальную карту, используя:
- Позиции планет в знаках и домах
- Основные аспекты (соединения, оппозиции, тригоны, квадраты)
- Текущие транзиты для прогнозов
- Стиль: мудрый наставник, но доступный язык
- Длина ответа: 2-3 абзаца максимум
- Фокус на практических советах и позитивном тоне
- Отвечай на русском языке
- В конце добавь краткий дисклеймер: прогноз носит развлекательный характер"""


class AIInterpreter:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.model = settings.openai_model
        self.calculator = ChartCalculator()

    async def _call_ai(self, user_prompt: str) -> str:
        if not self.client:
            return self._fallback_response(user_prompt)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=800,
                temperature=0.7,
            )
            return response.choices[0].message.content or self._fallback_response(user_prompt)
        except Exception:
            return self._fallback_response(user_prompt)

    def _fallback_response(self, prompt: str) -> str:
        if "совместим" in prompt.lower() or "синастр" in prompt.lower():
            return (
                "Ваши карты показывают интересную динамику! Энергии дополняют друг друга, "
                "создавая потенциал для глубокой связи. Обратите внимание на коммуникацию — "
                "это ключ к гармонии.\n\n"
                "⚠️ Прогноз носит развлекательный характер."
            )
        if "транзит" in prompt.lower() or "недел" in prompt.lower():
            return (
                "На этой неделе звёзды благоволят личностному росту. Юпитер поддерживает "
                "новые начинания, а Венера усиливает отношения. Используйте энергию четверга "
                "для важных решений.\n\n"
                "⚠️ Прогноз носит развлекательный характер."
            )
        if "сегодня" in prompt.lower() or "день" in prompt.lower():
            return (
                "Сегодня Луна создаёт благоприятные аспекты для саморефлексии. "
                "Уделите время тому, что приносит радость. Вечер подходит для общения "
                "с близкими.\n\n"
                "⚠️ Прогноз носит развлекательный характер."
            )
        return (
            "Ваша натальная карта раскрывает богатый внутренний мир. Солнце определяет "
            "вашу сущность, Луна — эмоциональную природу, а Асцендент — то, как вас "
            "воспринимают окружающие. Используйте свои сильные стороны для достижения целей.\n\n"
            "⚠️ Прогноз носит развлекательный характер."
        )

    async def interpret_natal(self, chart: NatalChart, name: str = "друг") -> str:
        chart_text = self.calculator.chart_to_text(chart)
        prompt = f"Проанализируй натальную карту для {name}:\n\n{chart_text}\n\nДай анализ личности, талантов и жизненных задач."
        return await self._call_ai(prompt)

    async def interpret_daily(self, chart: NatalChart, transits: list, name: str = "друг") -> str:
        chart_text = self.calculator.chart_to_text(chart)
        transit_text = "\n".join(
            f"  {t.planet1} {t.aspect_type} {t.planet2}" for t in transits[:8]
        ) or "  Спокойный день без сильных аспектов"
        prompt = (
            f"Дай персональный прогноз на сегодня для {name}.\n\n"
            f"Натальная карта:\n{chart_text}\n\n"
            f"Транзиты сегодня:\n{transit_text}"
        )
        return await self._call_ai(prompt)

    async def interpret_weekly(self, chart: NatalChart, name: str = "друг") -> str:
        chart_text = self.calculator.chart_to_text(chart)
        prompt = f"Дай прогноз на неделю для {name}:\n\n{chart_text}"
        return await self._call_ai(prompt)

    async def interpret_compatibility(
        self,
        chart1: NatalChart,
        chart2: NatalChart,
        name1: str = "Партнёр 1",
        name2: str = "Партнёр 2",
    ) -> str:
        text1 = self.calculator.chart_to_text(chart1)
        text2 = self.calculator.chart_to_text(chart2)
        prompt = (
            f"Проанализируй совместимость (синастрию) между {name1} и {name2}.\n\n"
            f"Карта {name1}:\n{text1}\n\n"
            f"Карта {name2}:\n{text2}"
        )
        return await self._call_ai(prompt)

    async def interpret_transits(self, chart: NatalChart, transits: list, name: str = "друг") -> str:
        chart_text = self.calculator.chart_to_text(chart)
        transit_text = "\n".join(
            f"  {t.planet1} {t.aspect_type} {t.planet2} (орб {t.orb}°)" for t in transits[:12]
        )
        prompt = (
            f"Опиши важные транзиты для {name}:\n\n"
            f"Натальная карта:\n{chart_text}\n\n"
            f"Активные транзиты:\n{transit_text}"
        )
        return await self._call_ai(prompt)

    async def answer_question(self, chart: NatalChart, question: str, name: str = "друг") -> str:
        chart_text = self.calculator.chart_to_text(chart)
        prompt = (
            f"Пользователь {name} задаёт вопрос астрологу: {question}\n\n"
            f"Натальная карта:\n{chart_text}\n\n"
            f"Ответь с точки зрения астрологии, опираясь на карту."
        )
        return await self._call_ai(prompt)
