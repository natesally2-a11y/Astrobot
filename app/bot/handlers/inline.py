"""Inline mode: quick compatibility & daily horoscopes for viral sharing."""
from __future__ import annotations

import datetime as dt
import hashlib

from aiogram import Router
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from app.astrology.constants import SIGNS, sign_index
from app.config import settings

router = Router(name="inline")

# Element compatibility groups.
_COMPATIBLE = {
    "Огонь": {"Огонь", "Воздух"},
    "Воздух": {"Воздух", "Огонь"},
    "Земля": {"Земля", "Вода"},
    "Вода": {"Вода", "Земля"},
}

_DAILY_THEMES = [
    "Отличный день для новых начинаний — действуйте смело.",
    "Прислушайтесь к интуиции, она подскажет верный путь.",
    "Хороший момент для общения и укрепления связей.",
    "Сосредоточьтесь на финансах и практичных делах.",
    "День благоприятен для творчества и самовыражения.",
    "Время позаботиться о себе и восстановить силы.",
    "Удача на стороне тех, кто проявляет терпение.",
]


def _bot_link(payload: str = "") -> InlineKeyboardMarkup:
    url = f"https://t.me/{settings.bot_username}"
    if payload:
        url += f"?start={payload}"
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔮 Открыть Stellarium AI", url=url)]]
    )


def _compat_text(i: int, j: int) -> str:
    a, b = SIGNS[i], SIGNS[j]
    el_a, el_b = a[3], b[3]
    if el_a == el_b:
        emoji, verdict = "🔥", "Очень высокая совместимость — родственные души!"
    elif el_b in _COMPATIBLE.get(el_a, set()):
        emoji, verdict = "💞", "Гармоничный союз с хорошим потенциалом."
    else:
        emoji, verdict = "⚡", "Притяжение противоположностей — страстно, но требует работы."
    return (
        f"{emoji} *Совместимость: {a[0]} {a[2]} + {b[0]} {b[2]}*\n\n"
        f"{verdict}\n\n"
        f"Стихии: {el_a} и {el_b}.\n\n"
        "_Хотите точный анализ по натальным картам? Откройте Stellarium AI._"
    )


def _daily_text(i: int) -> str:
    s = SIGNS[i]
    today = dt.date.today()
    seed = int(hashlib.md5(f"{i}-{today.isoformat()}".encode()).hexdigest(), 16)
    theme = _DAILY_THEMES[seed % len(_DAILY_THEMES)]
    return (
        f"⭐ *{s[0]} {s[2]} — прогноз на {today:%d.%m.%Y}*\n\n"
        f"{theme}\n\n"
        "_Персональный прогноз по вашей натальной карте — в Stellarium AI._"
    )


@router.inline_query()
async def inline_query(query: InlineQuery) -> None:
    text = query.query.strip().lower()
    tokens = text.split()
    results: list[InlineQueryResultArticle] = []

    signs = [sign_index(t) for t in tokens]
    signs = [s for s in signs if s is not None]

    if "compatibility" in tokens or "совместимость" in tokens or len(signs) >= 2:
        if len(signs) >= 2:
            content = _compat_text(signs[0], signs[1])
            results.append(
                InlineQueryResultArticle(
                    id="compat",
                    title=f"Совместимость {SIGNS[signs[0]][0]} + {SIGNS[signs[1]][0]}",
                    description="Нажмите, чтобы отправить результат",
                    input_message_content=InputTextMessageContent(
                        message_text=content, parse_mode="Markdown"
                    ),
                    reply_markup=_bot_link(),
                )
            )
    elif signs:
        idx = signs[0]
        results.append(
            InlineQueryResultArticle(
                id=f"daily-{idx}",
                title=f"Прогноз на сегодня — {SIGNS[idx][0]}",
                description="Нажмите, чтобы отправить",
                input_message_content=InputTextMessageContent(
                    message_text=_daily_text(idx), parse_mode="Markdown"
                ),
                reply_markup=_bot_link(),
            )
        )

    if not results:
        # Helpful default: list all signs' daily horoscope.
        for idx, s in enumerate(SIGNS):
            results.append(
                InlineQueryResultArticle(
                    id=f"daily-{idx}",
                    title=f"{s[2]} {s[0]} — прогноз на сегодня",
                    description="Нажмите, чтобы отправить",
                    input_message_content=InputTextMessageContent(
                        message_text=_daily_text(idx), parse_mode="Markdown"
                    ),
                    reply_markup=_bot_link(),
                )
            )

    await query.answer(results, cache_time=300, is_personal=False)
