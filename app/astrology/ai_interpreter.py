from __future__ import annotations

from datetime import date
from typing import Optional

from openai import AsyncOpenAI

from app.astrology.calculations import NatalChart
from app.config import get_settings

settings = get_settings()


class AstrologyAIInterpreter:
    def __init__(self) -> None:
        self._client: Optional[AsyncOpenAI] = None
        if settings.openai_api_key:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def interpret_natal(self, chart: NatalChart) -> str:
        prompt = (
            "Ты профессиональный астролог с 20-летним опытом. "
            "Сделай короткий разбор натальной карты (2-3 абзаца), "
            "мудро и практично, с позитивным тоном."
        )
        payload = (
            f"Солнечный знак: {chart.sun_sign}\n"
            f"Планеты: {', '.join(f'{p.name} в {p.sign}, дом {p.house}' for p in chart.planets)}"
        )
        return await self._run_or_fallback(prompt, payload)

    async def forecast_today(self, chart: NatalChart, transit_text: str, target_day: date) -> str:
        prompt = (
            "Дай персональный астропрогноз на день на основе натальной карты и транзитов. "
            "2-3 абзаца, фокус на практических шагах."
        )
        payload = (
            f"Дата прогноза: {target_day.isoformat()}\n"
            f"Солнечный знак: {chart.sun_sign}\n"
            f"Транзит: {transit_text}"
        )
        return await self._run_or_fallback(prompt, payload)

    async def compatibility(self, chart_a: NatalChart, chart_b: NatalChart, base_snapshot: str) -> str:
        prompt = (
            "Сделай разбор совместимости двух людей, используй понятный язык. "
            "2-3 абзаца: сильные стороны союза, зоны риска, практический совет."
        )
        payload = (
            f"Человек A: {chart_a.sun_sign}\n"
            f"Человек B: {chart_b.sun_sign}\n"
            f"Базовая оценка: {base_snapshot}"
        )
        return await self._run_or_fallback(prompt, payload)

    async def answer_question(self, chart: NatalChart, question: str) -> str:
        prompt = (
            "Ответь как ИИ-астролог на вопрос пользователя с учетом его натальной карты. "
            "Максимум 2 абзаца и 1 практический совет."
        )
        payload = f"Солнечный знак: {chart.sun_sign}\nВопрос: {question}"
        return await self._run_or_fallback(prompt, payload)

    async def _run_or_fallback(self, system_prompt: str, payload: str) -> str:
        if not self._client:
            return (
                "Пока AI-режим работает в демо-формате. "
                f"Базовый разбор: {payload[:220]}...\n\n"
                "Совет: фиксируйте настроение и события в течение недели, "
                "чтобы точнее калибровать прогнозы."
            )

        completion = await self._client.responses.create(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": payload},
            ],
            temperature=0.7,
        )
        return completion.output_text

