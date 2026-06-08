from __future__ import annotations

from datetime import date

from openai import AsyncOpenAI

from app.astrology.calculations import calculate_transits, compatibility_by_signs, describe_chart_short, planet_table
from app.astrology.schemas import NatalChart
from app.config import get_settings
from app.legal import ASTROLOGY_DISCLAIMER

SYSTEM_PROMPT = (
    "Ты — профессиональный астролог с 20-летним опытом. Анализируй натальную карту, используя:\n"
    "- Позиции планет в знаках и домах\n"
    "- Основные аспекты: соединения, оппозиции, тригоны, квадраты и секстили\n"
    "- Текущие транзиты для прогнозов\n"
    "- Стиль: мудрый наставник, но доступный язык\n"
    "- Длина ответа: 2-3 абзаца максимум\n"
    "- Фокус на практических советах и позитивном тоне\n"
    "- Обязательно помни, что астрология носит развлекательный характер."
)


class AIInterpreter:
    def __init__(self) -> None:
        settings = get_settings()
        api_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else ""
        self.model = settings.openai_model
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None

    async def _complete(self, prompt: str, fallback: str) -> str:
        if self.client is None:
            return fallback
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.75,
            max_tokens=700,
        )
        content = response.choices[0].message.content
        return content.strip() if content else fallback

    async def natal_reading(self, chart: NatalChart) -> str:
        prompt = (
            "Сделай базовую интерпретацию натальной карты для нового пользователя.\n"
            f"Краткое ядро: {describe_chart_short(chart)}\n"
            f"Планеты: {planet_table(chart)}\n"
            f"Аспекты: {[aspect.__dict__ for aspect in chart.aspects[:10]]}"
        )
        fallback = (
            f"Ваше астрологическое ядро: {describe_chart_short(chart)}. Это сочетание показывает, "
            "как вы проявляете волю, эмоционально реагируете и выбираете направление развития.\n\n"
            "Сегодня полезно воспринимать карту как язык самонаблюдения: отмечайте повторяющиеся "
            "темы, сильные стороны и зоны роста. Используйте прогнозы как повод задать себе точные "
            "вопросы, а не как жесткий сценарий будущего."
        )
        return await self._complete(prompt, fallback)

    async def daily_forecast(self, chart: NatalChart, target_date: date | None = None) -> str:
        transits = calculate_transits(chart, target_date)
        prompt = (
            "Сделай персональный прогноз на день по натальной карте и текущим транзитам.\n"
            f"Дата: {target_date or date.today()}\n"
            f"Карта: {describe_chart_short(chart)}\n"
            f"Транзиты: {[transit.__dict__ for transit in transits]}"
        )
        if transits:
            top = transits[0]
            transit_text = (
                f"Главный акцент дня: {top.transit_planet} в аспекте {top.aspect} "
                f"к натальной планете {top.natal_planet}."
            )
        else:
            transit_text = "День выглядит ровным: сильных точных транзитов не найдено."
        fallback = (
            f"{transit_text} Используйте этот день для спокойной настройки на свои цели и "
            "не перегружайте себя решениями, которые требуют холодного расчета.\n\n"
            "Практика дня: выберите один приоритет и завершите его до конца. Такой фокус поможет "
            "прожить транзиты конструктивно и заметить, где интуиция подсказывает верное направление."
        )
        return await self._complete(prompt, fallback)

    async def weekly_forecast(self, chart: NatalChart) -> str:
        prompt = (
            "Сделай прогноз на неделю для Premium-пользователя. Дай 3 ключевые темы недели.\n"
            f"Карта: {describe_chart_short(chart)}\n"
            f"Планеты: {planet_table(chart)}"
        )
        fallback = (
            "На этой неделе главный фокус — выравнивание личных целей и повседневных обязательств. "
            "Старайтесь не распыляться: ваша карта лучше раскрывается через последовательность.\n\n"
            "Три ориентира: завершите старый хвост, выделите время на восстановление и обсудите важный "
            "вопрос без давления. Такой ритм даст больше ясности, чем попытка решить все сразу."
        )
        return await self._complete(prompt, fallback)

    async def compatibility(self, left: NatalChart, right: NatalChart) -> str:
        summary = compatibility_by_signs(left, right)
        prompt = (
            "Сделай краткий анализ совместимости по двум картам. Укажи сильную сторону пары и зону риска.\n"
            f"База совместимости: {summary}\n"
            f"Карта 1: {planet_table(left)}\n"
            f"Карта 2: {planet_table(right)}"
        )
        fallback = (
            f"{summary} Сильная сторона пары — способность учиться друг у друга и расширять привычный "
            "взгляд на отношения.\n\n"
            "Зона внимания — разные способы реагировать на стресс. Договоритесь заранее, как вы берете "
            "паузу, возвращаетесь к диалогу и поддерживаете друг друга без давления."
        )
        return await self._complete(prompt, fallback)

    async def answer_question(self, chart: NatalChart, question: str) -> str:
        prompt = (
            "Ответь на вопрос пользователя как персональный ИИ-астролог. Не давай медицинских, "
            "финансовых или юридических инструкций.\n"
            f"Карта: {describe_chart_short(chart)}\n"
            f"Вопрос: {question}"
        )
        fallback = (
            f"С точки зрения вашей карты ({describe_chart_short(chart)}) вопрос лучше рассматривать "
            "через призму личной ответственности и наблюдения за повторяющимися сценариями.\n\n"
            "Попробуйте сформулировать один маленький шаг, который зависит только от вас. Астрология "
            "здесь может быть зеркалом для размышления, но важные решения стоит сверять с реальностью "
            "и советами профильных специалистов."
        )
        return await self._complete(prompt, fallback)


def disclaimer_suffix() -> str:
    return f"\n\n{ASTROLOGY_DISCLAIMER}"
