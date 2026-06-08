import json

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.inline import confirm_delete_keyboard, settings_keyboard, start_keyboard
from app.database import crud

router = Router()

PRIVACY_TEXT = """📄 **Политика конфиденциальности**

Stellarium AI обрабатывает персональные данные в соответствии с GDPR и ФЗ-152.

**Какие данные мы собираем:**
• Дата, время и место рождения
• Имя и Telegram ID
• История астрологических чтений

**Цели обработки:**
• Расчёт натальной карты
• Персонализированные прогнозы
• Управление подпиской

**Ваши права:**
• /my_data — просмотр данных
• /export_data — экспорт в JSON
• /delete_data — полное удаление

Мы не передаём данные третьим лицам.

Полная версия: privacy_policy.md"""


@router.message(Command("privacy"))
async def cmd_privacy(message: Message) -> None:
    await message.answer(PRIVACY_TEXT, parse_mode="Markdown")


@router.message(Command("my_data"))
async def cmd_my_data(message: Message, session: AsyncSession) -> None:
    data = await crud.export_user_data(session, message.from_user.id)
    if not data:
        await message.answer("Данные не найдены. Используйте /start для регистрации.")
        return
    bd = data.get("birth_data")
    text = "📋 **Ваши сохранённые данные**\n\n"
    if bd:
        text += f"📅 Дата рождения: {bd['birth_date']}\n"
        text += f"⏰ Время: {bd.get('birth_time', 'не указано')}\n"
        text += f"📍 Место: {bd['birth_place']}\n"
    text += f"\n💎 Подписка: {data['user']['subscription_type']}"
    text += f"\n📚 Чтений: {len(data.get('readings', []))}"
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("export_data"))
async def cmd_export_data(message: Message, session: AsyncSession) -> None:
    data = await crud.export_user_data(session, message.from_user.id)
    if not data:
        await message.answer("Нет данных для экспорта.")
        return
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    file = BufferedInputFile(json_str.encode("utf-8"), filename="stellarium_data.json")
    await message.answer_document(file, caption="📤 Экспорт ваших данных (GDPR)")


@router.message(Command("delete_data"))
async def cmd_delete_data(message: Message) -> None:
    await message.answer(
        "⚠️ Вы уверены, что хотите удалить ВСЕ данные?\n"
        "Это действие необратимо.",
        reply_markup=confirm_delete_keyboard(),
    )


@router.callback_query(F.data == "export_data")
async def callback_export(callback: CallbackQuery, session: AsyncSession) -> None:
    data = await crud.export_user_data(session, callback.from_user.id)
    if not data:
        await callback.answer("Нет данных")
        return
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    file = BufferedInputFile(json_str.encode("utf-8"), filename="stellarium_data.json")
    await callback.message.answer_document(file, caption="📤 Экспорт данных")
    await callback.answer()


@router.callback_query(F.data == "delete_data_confirm")
async def callback_delete_confirm(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "⚠️ Удалить все данные безвозвратно?",
        reply_markup=confirm_delete_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "delete_data_yes")
async def callback_delete_yes(callback: CallbackQuery, session: AsyncSession) -> None:
    deleted = await crud.delete_user_data(session, callback.from_user.id)
    if deleted:
        await callback.message.answer(
            "✅ Все ваши данные удалены. Спасибо, что были с нами!\n"
            "Используйте /start для новой регистрации.",
            reply_markup=start_keyboard(),
        )
    else:
        await callback.message.answer("Данные не найдены.")
    await callback.answer()


@router.callback_query(F.data == "privacy_policy")
async def callback_privacy(callback: CallbackQuery) -> None:
    await callback.message.answer(PRIVACY_TEXT, parse_mode="Markdown")
    await callback.answer()
