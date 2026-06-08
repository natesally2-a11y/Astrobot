"""Inline mode for viral growth.

Usage examples (typed in any chat):

    @stellarium_ai_bot compatibility Leo Scorpio
    @stellarium_ai_bot daily Virgo
    @stellarium_ai_bot Aries
"""

from __future__ import annotations

import hashlib
import logging

from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from app.astrology.calculations import SIGNS_RU

router = Router(name="inline")
logger = logging.getLogger(__name__)

SIGN_ALIASES = {
    "aries": "Овен", "овен": "Овен",
    "taurus": "Телец", "телец": "Телец",
    "gemini": "Близнецы", "близнецы": "Близнецы",
    "cancer": "Рак", "рак": "Рак",
    "leo": "Лев", "лев": "Лев",
    "virgo": "Дева", "дева": "Дева",
    "libra": "Весы", "весы": "Весы",
    "scorpio": "Скорпион", "скорпион": "Скорпион",
    "sagittarius": "Стрелец", "стрелец": "Стрелец",
    "capricorn": "Козерог", "козерог": "Козерог",
    "aquarius": "Водолей", "водолей": "Водолей",
    "pisces": "Рыбы", "рыбы": "Рыбы",
}

DAILY_BLURBS = {
    "Овен": "⭐ Энергия бьёт ключом — берите инициативу.",
    "Телец": "🌿 Хороший день для финансовых решений и заботы о теле.",
    "Близнецы": "💬 Контакты и идеи открывают неожиданные двери.",
    "Рак": "🌙 Доверяйте интуиции и проведите время с близкими.",
    "Лев": "🔥 Время блеска: проявите себя и поделитесь теплом.",
    "Дева": "📋 Систематизируйте дела — мелочи дадут большой результат.",
    "Весы": "⚖️ Гармония в отношениях возможна через откровенный разговор.",
    "Скорпион": "🌊 Глубокие инсайты — слушайте свои чувства.",
    "Стрелец": "🏹 Откройте новый горизонт — учёба и путешествия в фаворе.",
    "Козерог": "🏔 Маленький шаг сегодня — большая победа завтра.",
    "Водолей": "💡 Идея, которая давно крутится в голове, готова к старту.",
    "Рыбы": "🐟 Творчество и эмпатия выведут вас вперёд.",
}

COMPAT_GRID = {
    ("Овен", "Лев"): "🔥 Огненная страсть и общие цели.",
    ("Лев", "Скорпион"): "🔥 Страстный союз с глубокими эмоциями.",
    ("Дева", "Телец"): "🌿 Уютный, надёжный союз земли и труда.",
    ("Близнецы", "Водолей"): "💨 Лёгкость и интеллектуальное взаимопонимание.",
    ("Рак", "Рыбы"): "🌊 Эмоциональная глубина и забота друг о друге.",
}


def _norm(token: str) -> str | None:
    return SIGN_ALIASES.get(token.strip().lower())


def _compat_text(a: str, b: str) -> str:
    text = COMPAT_GRID.get((a, b)) or COMPAT_GRID.get((b, a))
    if text:
        return f"Совместимость {a} и {b}: {text}"
    return (
        f"Совместимость {a} и {b}: интересный союз — стоит исследовать"
        " натальные карты, чтобы увидеть детали. Откройте @stellarium_ai_bot"
        " для персонального анализа."
    )


def _make_result(title: str, text: str) -> InlineQueryResultArticle:
    rid = hashlib.md5(f"{title}|{text}".encode("utf-8")).hexdigest()[:32]
    return InlineQueryResultArticle(
        id=rid,
        title=title,
        description=text[:120],
        input_message_content=InputTextMessageContent(message_text=text),
    )


@router.inline_query()
async def inline_query(query: InlineQuery) -> None:
    text = (query.query or "").strip()
    results: list[InlineQueryResultArticle] = []

    if not text:
        for sign in SIGNS_RU:
            blurb = DAILY_BLURBS.get(sign, "")
            results.append(_make_result(f"Гороскоп для {sign}", f"Сегодня для {sign}: {blurb}"))
        await query.answer(results=results[:20], cache_time=60, is_personal=False)
        return

    tokens = text.split()
    cmd = tokens[0].lower()

    if cmd in {"compat", "compatibility", "совместимость"} and len(tokens) >= 3:
        a, b = _norm(tokens[1]), _norm(tokens[2])
        if a and b:
            results.append(_make_result(f"{a} ↔ {b}", _compat_text(a, b)))
    elif cmd in {"daily", "today", "сегодня"} and len(tokens) >= 2:
        sign = _norm(tokens[1])
        if sign:
            blurb = DAILY_BLURBS.get(sign, "")
            results.append(
                _make_result(f"Сегодня для {sign}", f"Сегодня для {sign}: {blurb}")
            )
    else:
        sign = _norm(tokens[0])
        if sign:
            blurb = DAILY_BLURBS.get(sign, "")
            results.append(_make_result(f"Гороскоп для {sign}", f"Сегодня для {sign}: {blurb}"))
            if len(tokens) >= 2:
                other = _norm(tokens[1])
                if other:
                    results.append(_make_result(
                        f"Совместимость {sign} ↔ {other}",
                        _compat_text(sign, other),
                    ))

    if not results:
        results.append(_make_result(
            "Stellarium AI",
            "Попробуйте: `daily Лев`, `compat Лев Скорпион` или просто `Дева`.",
        ))
    await query.answer(results=results[:20], cache_time=30, is_personal=False)
