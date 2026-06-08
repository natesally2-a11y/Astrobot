import json

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot.utils.texts import PRIVACY_SUMMARY
from app.database.crud import delete_user_data, export_user_data
from app.database.session import async_session

router = Router(name="data_rights")


@router.message(Command("privacy"))
async def privacy_command(message: Message) -> None:
    await message.answer(PRIVACY_SUMMARY)


@router.message(Command("my_data"))
async def my_data_command(message: Message) -> None:
    if message.from_user is None:
        return
    async with async_session() as session:
        data = await export_user_data(session, message.from_user.id)

    if data is None:
        await message.answer("Мы не нашли сохраненных данных для вашего Telegram ID.")
        return

    birth_data = data.get("birth_data") or {}
    await message.answer(
        "Ваши сохраненные данные:\n"
        f"Telegram ID: {data['telegram_id']}\n"
        f"Имя: {data.get('first_name')}\n"
        f"Username: {data.get('username')}\n"
        f"Тариф: {data.get('subscription_type')}\n"
        f"Согласие GDPR/ФЗ-152: {data.get('gdpr_consent')}\n"
        f"Дата рождения: {birth_data.get('birth_date')}\n"
        f"Время рождения: {birth_data.get('birth_time')}\n"
        f"Место рождения: {birth_data.get('birth_place')}\n"
        f"Количество чтений: {len(data.get('readings', []))}"
    )


@router.message(Command("export_data"))
async def export_data_command(message: Message) -> None:
    await _send_export(message)


@router.callback_query(F.data == "data:export")
async def export_data_callback(callback: CallbackQuery) -> None:
    if callback.message:
        await _send_export(callback.message, callback.from_user.id)
    await callback.answer()


@router.message(Command("delete_data"))
async def delete_data_command(message: Message) -> None:
    await message.answer(
        "Удалить аккаунт, натальные данные, историю чтений и подписочные записи? Это действие необратимо.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Да, удалить все данные", callback_data="data:delete_confirm")],
                [InlineKeyboardButton(text="Отмена", callback_data="data:delete_cancel")],
            ]
        ),
    )


@router.callback_query(F.data == "data:delete_confirm")
async def delete_data_confirm(callback: CallbackQuery) -> None:
    async with async_session() as session:
        await delete_user_data(session, callback.from_user.id)
    await callback.message.answer("Все данные удалены. Чтобы начать заново, используйте /start.")
    await callback.answer()


@router.callback_query(F.data == "data:delete_cancel")
async def delete_data_cancel(callback: CallbackQuery) -> None:
    await callback.message.answer("Удаление отменено.")
    await callback.answer()


async def _send_export(message: Message, user_id: int | None = None) -> None:
    effective_user_id = user_id or (message.from_user.id if message.from_user else None)
    if effective_user_id is None:
        return

    async with async_session() as session:
        data = await export_user_data(session, effective_user_id)

    if data is None:
        await message.answer("Экспорт пуст: сохраненных данных нет.")
        return

    payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    await message.answer_document(
        BufferedInputFile(payload, filename="stellarium_ai_data_export.json"),
        caption="Ваш экспорт данных в формате JSON.",
    )
