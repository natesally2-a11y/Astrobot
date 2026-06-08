"""GDPR / 152-ФЗ data management commands."""
from __future__ import annotations

import json

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import texts
from app.bot.keyboards.inline import delete_confirm_keyboard
from app.database import crud
from app.database.models import User

router = Router(name="gdpr")


@router.message(Command("privacy"))
async def cmd_privacy(message: Message) -> None:
    await message.answer(texts.PRIVACY_SHORT, parse_mode="Markdown")


@router.callback_query(F.data == "gdpr:policy")
async def cb_policy(callback: CallbackQuery) -> None:
    await callback.message.answer(texts.PRIVACY_SHORT, parse_mode="Markdown")
    await callback.answer()


def _format_my_data(data: dict) -> str:
    if not data:
        return texts.NEED_PROFILE
    u = data["user"]
    bd = data.get("birth_data")
    lines = ["📂 *Ваши сохранённые данные*\n"]
    lines.append(f"Имя: {u.get('first_name') or '—'}")
    lines.append(f"Тариф: {u.get('subscription_type')}")
    lines.append(f"Согласие GDPR: {'да' if u.get('gdpr_consent') else 'нет'}")
    if bd:
        lines.append("\n*Данные рождения:*")
        lines.append(f"Дата: {bd.get('birth_date')}")
        lines.append(f"Время: {bd.get('birth_time') or 'неизвестно'}")
        lines.append(f"Место: {bd.get('birth_place')}")
        if bd.get("latitude") is not None:
            lines.append(f"Координаты: {bd.get('latitude'):.4f}, {bd.get('longitude'):.4f}")
        lines.append(f"Часовой пояс: {bd.get('timezone') or '—'}")
    lines.append(f"\nВсего чтений в истории: {len(data.get('readings', []))}")
    lines.append("\nЭкспорт в JSON — /export\\_data\nУдалить всё — /delete\\_data")
    return "\n".join(lines)


@router.message(Command("my_data"))
async def cmd_my_data(message: Message, session: AsyncSession, user: User) -> None:
    data = await crud.export_user_data(session, user.telegram_id)
    await message.answer(_format_my_data(data), parse_mode="Markdown")


@router.callback_query(F.data == "gdpr:mydata")
async def cb_my_data(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    data = await crud.export_user_data(session, user.telegram_id)
    await callback.message.answer(_format_my_data(data), parse_mode="Markdown")
    await callback.answer()


@router.message(Command("export_data"))
async def cmd_export(message: Message, session: AsyncSession, user: User) -> None:
    data = await crud.export_user_data(session, user.telegram_id)
    if not data:
        await message.answer(texts.NEED_PROFILE)
        return
    payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    doc = BufferedInputFile(payload, filename=f"stellarium_data_{user.telegram_id}.json")
    await message.answer_document(
        doc, caption="📤 Экспорт ваших данных (GDPR — право на переносимость)."
    )


@router.message(Command("delete_data"))
async def cmd_delete(message: Message) -> None:
    await message.answer(
        texts.DELETE_CONFIRM, parse_mode="Markdown", reply_markup=delete_confirm_keyboard()
    )


@router.callback_query(F.data == "gdpr:delete_confirm")
async def cb_delete_confirm(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    await crud.delete_user_data(session, user.telegram_id)
    await callback.message.edit_text(texts.DELETE_DONE)
    await callback.answer("Данные удалены")
