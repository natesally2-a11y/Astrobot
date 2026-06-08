"""GDPR / 152-ФЗ: управление персональными данными."""
from __future__ import annotations

import json

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import texts
from app.bot.keyboards.common import delete_confirm_keyboard
from app.database import crud

router = Router(name="gdpr")


@router.message(Command("privacy"))
async def cmd_privacy(message: Message) -> None:
    await message.answer(texts.PRIVACY_SHORT)


@router.callback_query(F.data == "gdpr:policy")
async def cb_policy(call: CallbackQuery) -> None:
    await call.answer()
    await call.message.answer(texts.PRIVACY_SHORT)


@router.message(Command("my_data"))
async def cmd_my_data(message: Message, session: AsyncSession) -> None:
    data = await crud.export_user_data(session, message.from_user.id)
    if not data:
        await message.answer(texts.NO_DATA)
        return
    u = data["user"]
    bd = data.get("birth_data")
    lines = [
        "📂 <b>Ваши сохранённые данные</b>\n",
        f"ID: <code>{u['telegram_id']}</code>",
        f"Имя: {u.get('first_name') or '—'}",
        f"Username: @{u['username']}" if u.get("username") else "Username: —",
        f"Тариф: {u['subscription_type']}",
        f"Согласие GDPR: {'да' if u['gdpr_consent'] else 'нет'}",
    ]
    if bd:
        lines.append(
            f"\nРождение: {bd['birth_date']} {bd.get('birth_time') or '—'}\n"
            f"Место: {bd['birth_place']}\n"
            f"Координаты: {bd.get('latitude')}, {bd.get('longitude')}\n"
            f"Часовой пояс: {bd.get('timezone') or '—'}"
        )
    lines.append(f"\nСохранено чтений: {len(data.get('readings', []))}")
    lines.append("\nЭкспорт в JSON — /export_data\nУдаление — /delete_data")
    await message.answer("\n".join(lines))


@router.message(Command("export_data"))
async def cmd_export_data(message: Message, session: AsyncSession) -> None:
    data = await crud.export_user_data(session, message.from_user.id)
    if not data:
        await message.answer(texts.NO_DATA)
        return
    payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    doc = BufferedInputFile(payload, filename="stellarium_data.json")
    await message.answer_document(
        doc,
        caption="📦 Экспорт ваших данных (GDPR — право на переносимость).",
    )


@router.message(Command("delete_data"))
async def cmd_delete_data(message: Message) -> None:
    await message.answer(texts.DELETE_CONFIRM, reply_markup=delete_confirm_keyboard())


@router.callback_query(F.data == "gdpr:delete_confirm")
async def cb_delete_confirm(call: CallbackQuery, session: AsyncSession) -> None:
    await crud.delete_user_data(session, call.from_user.id)
    await call.message.edit_text(texts.DELETED)
    await call.answer("Данные удалены")


@router.callback_query(F.data == "gdpr:delete_cancel")
async def cb_delete_cancel(call: CallbackQuery) -> None:
    await call.message.edit_text("Удаление отменено. Ваши данные сохранены. ✅")
    await call.answer()
