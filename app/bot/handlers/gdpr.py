"""GDPR / ФЗ-152 commands."""
from __future__ import annotations

import io
import json
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    Message,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import texts
from app.bot.states import Onboarding
from app.database.crud import (
    delete_user,
    get_birth_data,
    list_readings,
    set_gdpr_consent,
)
from app.database.models import User

router = Router(name="gdpr")


@router.callback_query(F.data == "gdpr:accept")
async def cb_consent_accept(
    cq: CallbackQuery, state: FSMContext, session: AsyncSession, user: User
) -> None:
    await set_gdpr_consent(session, user)
    await cq.message.edit_reply_markup(reply_markup=None)
    await cq.message.answer(
        "Спасибо! 🌌 Теперь скажите, как мне к вам обращаться?"
    )
    await state.set_state(Onboarding.waiting_name)
    await cq.answer()


@router.callback_query(F.data == "gdpr:policy")
async def cb_show_policy(cq: CallbackQuery) -> None:
    await cq.message.answer(texts.PRIVACY_SHORT)
    await cq.answer()


@router.message(Command("privacy"))
async def cmd_privacy(message: Message) -> None:
    await message.answer(texts.PRIVACY_SHORT)


@router.message(Command("privacy_full"))
async def cmd_privacy_full(message: Message) -> None:
    from pathlib import Path

    path = Path("docs/privacy_policy.md")
    if path.exists():
        body = path.read_text(encoding="utf-8")
        # Telegram message limit ≈4096 chars.
        for chunk in _split_chunks(body, 3800):
            await message.answer(chunk)
    else:
        await message.answer(texts.PRIVACY_SHORT)


@router.message(Command("my_data"))
async def cmd_my_data(message: Message, session: AsyncSession, user: User) -> None:
    bd = await get_birth_data(session, user.telegram_id)
    text = [
        "📦 <b>Ваши данные:</b>",
        f"• Telegram ID: <code>{user.telegram_id}</code>",
        f"• Имя в Telegram: {user.first_name or '—'}",
        f"• Подписка: {user.subscription_type}",
        f"• Согласие GDPR: {'да' if user.gdpr_consent else 'нет'}",
    ]
    if bd:
        text.append("")
        text.append("<b>Натальные данные:</b>")
        text.append(f"• Имя: {bd.name or '—'}")
        text.append(f"• Дата рождения: {bd.birth_date}")
        text.append(
            f"• Время рождения: {bd.birth_time if not bd.time_is_unknown else 'неизвестно'}"
        )
        text.append(f"• Место: {bd.birth_place}")
        text.append(f"• Координаты: {bd.latitude}, {bd.longitude}")
        text.append(f"• Часовой пояс: {bd.timezone or '—'}")
    else:
        text.append("\nНатальные данные ещё не введены.")
    await message.answer("\n".join(text), parse_mode="HTML")


@router.message(Command("export_data"))
async def cmd_export_data(message: Message, session: AsyncSession, user: User) -> None:
    bd = await get_birth_data(session, user.telegram_id)
    readings = await list_readings(session, user.telegram_id, limit=200)

    payload = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "user": {
            "telegram_id": user.telegram_id,
            "first_name": user.first_name,
            "username": user.username,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "subscription_type": user.subscription_type,
            "subscription_expires_at": (
                user.subscription_expires_at.isoformat()
                if user.subscription_expires_at
                else None
            ),
            "gdpr_consent": user.gdpr_consent,
        },
        "birth_data": (
            None
            if bd is None
            else {
                "name": bd.name,
                "birth_date": bd.birth_date.isoformat(),
                "birth_time": (
                    None if bd.time_is_unknown else bd.birth_time.isoformat()
                ),
                "birth_place": bd.birth_place,
                "latitude": float(bd.latitude) if bd.latitude is not None else None,
                "longitude": float(bd.longitude) if bd.longitude is not None else None,
                "timezone": bd.timezone,
            }
        ),
        "readings": [
            {
                "type": r.reading_type,
                "question": r.question,
                "response": r.ai_response,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in readings
        ],
    }
    data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    file = BufferedInputFile(data, filename="stellarium_export.json")
    await message.answer_document(
        file, caption="Ваш экспорт данных (GDPR Right to portability)."
    )


@router.message(Command("delete_data"))
async def cmd_delete_data_prompt(message: Message) -> None:
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    kb = InlineKeyboardBuilder()
    kb.button(text="🗑 Да, удалить", callback_data="gdpr:delete:yes")
    kb.button(text="Отмена", callback_data="gdpr:delete:no")
    kb.adjust(2)
    await message.answer(
        "Вы уверены? Это удалит все ваши данные (натальную карту, историю "
        "запросов, статус подписки). Действие необратимо.",
        reply_markup=kb.as_markup(),
    )


@router.callback_query(F.data == "gdpr:delete:no")
async def cb_delete_cancel(cq: CallbackQuery) -> None:
    await cq.message.edit_text("Удаление отменено.")
    await cq.answer()


@router.callback_query(F.data == "gdpr:delete:yes")
async def cb_delete_confirm(cq: CallbackQuery, session: AsyncSession, user: User) -> None:
    await delete_user(session, user.telegram_id)
    await cq.message.edit_text(
        "Готово. Все ваши данные удалены. Если захотите вернуться — /start."
    )
    await cq.answer()


def _split_chunks(text: str, size: int):
    for i in range(0, len(text), size):
        yield text[i : i + size]
