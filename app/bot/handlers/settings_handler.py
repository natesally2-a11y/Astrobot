"""Handler for /settings, /help, and GDPR commands."""

import json

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from app.database.crud import (
    get_user,
    get_birth_data,
    check_subscription_level,
    export_user_data,
    delete_user_data,
)
from app.bot.keyboards.inline import (
    settings_keyboard,
    subscription_keyboard,
    confirm_delete_keyboard,
    back_to_settings_keyboard,
    start_keyboard,
)

router = Router()

HELP_TEXT = """📚 <b>Команды Stellarium AI</b>

🌟 <b>Основные:</b>
/start — Приветствие и регистрация
/chart — Показать натальную карту
/today — Персональный прогноз на сегодня
/week — Прогноз на неделю ⭐
/compatibility — Совместимость с партнёром
/ask — Задать вопрос астрологу
/transit — Важные транзиты ⭐
/settings — Настройки и подписка

🔒 <b>Приватность:</b>
/privacy — Политика конфиденциальности
/my_data — Показать сохранённые данные
/export_data — Экспорт данных в JSON
/delete_data — Удалить аккаунт

⭐ — доступно по подписке Pro / Oracle

⚠️ <i>Астрологические прогнозы носят исключительно развлекательный характер и не являются руководством к действию. Не используйте астрологию для принятия важных жизненных, медицинских или финансовых решений.</i>

<i>Stellarium AI создан для саморазвития и развлечения.</i>"""

DISCLAIMER = """⚠️ <b>Важно</b>

Астрологические прогнозы носят исключительно развлекательный характер и не являются руководством к действию.

Не используйте астрологию для принятия важных жизненных, медицинских или финансовых решений. При серьёзных проблемах обращайтесь к квалифицированным специалистам.

Stellarium AI создан для саморазвития и развлечения."""


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(HELP_TEXT, parse_mode="HTML")


@router.message(Command("settings"))
async def cmd_settings(message: Message):
    if not message.from_user:
        return
    await message.answer(
        "⚙️ <b>Настройки</b>",
        reply_markup=settings_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "settings_back")
async def settings_back(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>",
        reply_markup=settings_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "my_profile")
async def my_profile(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    if not user:
        await callback.answer("Профиль не найден", show_alert=True)
        return

    bd = await get_birth_data(callback.from_user.id)
    level = await check_subscription_level(callback.from_user.id)

    plan_names = {"free": "Бесплатный", "pro": "Stellarium Pro ⭐", "oracle": "Космический Оракул 🔮"}

    text = f"👤 <b>Профиль</b>\n\n"
    text += f"Имя: {user.first_name or '—'}\n"
    text += f"Username: @{user.username}\n" if user.username else ""
    text += f"Подписка: {plan_names.get(level, level)}\n"

    if user.subscription_expires_at and level != "free":
        text += f"Действует до: {user.subscription_expires_at.strftime('%d.%m.%Y')}\n"

    if bd:
        text += f"\n📅 Дата рождения: {bd.birth_date.strftime('%d.%m.%Y')}\n"
        if bd.birth_time:
            text += f"⏰ Время: {bd.birth_time.strftime('%H:%M')}\n"
        text += f"📍 Место: {bd.birth_place}\n"

    text += f"\nРеферальная ссылка:\n<code>t.me/stellarium_ai_bot?start=ref_{callback.from_user.id}</code>"

    await callback.message.edit_text(text, reply_markup=back_to_settings_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "manage_subscription")
async def manage_subscription(callback: CallbackQuery):
    level = await check_subscription_level(callback.from_user.id)
    plan_names = {"free": "Бесплатный", "pro": "Stellarium Pro ⭐", "oracle": "Космический Оракул 🔮"}

    text = f"⭐ <b>Подписка</b>\n\nТекущий план: {plan_names.get(level, level)}\n\n"

    if level == "free":
        text += "Обновите для получения полного доступа:"
    else:
        text += "Вы можете изменить план:"

    await callback.message.edit_text(text, reply_markup=subscription_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "compare_plans")
async def compare_plans(callback: CallbackQuery):
    text = """📋 <b>Сравнение планов</b>

<b>🆓 Бесплатный:</b>
• Натальная карта
• Базовый анализ личности
• Краткий ежедневный прогноз
• 5 вопросов ИИ в день

<b>⭐ Stellarium Pro (50 Stars/мес):</b>
• Подробные ежедневные прогнозы
• Недельные и месячные прогнозы
• Совместимость (до 3 партнёров)
• Безлимитные вопросы ИИ
• Уведомления о транзитах

<b>🔮 Космический Оракул (150 Stars/мес):</b>
• Всё из Pro +
• Бизнес-астрология
• Годовые прогнозы
• Индивидуальные рекомендации
• Приоритетная поддержка ИИ"""

    await callback.message.edit_text(text, reply_markup=subscription_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "edit_birth_data")
async def edit_birth_data(callback: CallbackQuery):
    from app.bot.keyboards.inline import birth_date_year_keyboard
    await callback.message.edit_text(
        "📅 <b>Изменение данных рождения</b>\n\nВыберите десятилетие:",
        reply_markup=birth_date_year_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


# --- GDPR commands ---

@router.message(Command("privacy"))
async def cmd_privacy(message: Message):
    await message.answer(
        "📄 <b>Политика конфиденциальности Stellarium AI</b>\n\n"
        "Мы обрабатываем следующие данные:\n"
        "• Telegram ID и имя пользователя\n"
        "• Дата, время и место рождения\n"
        "• История астрологических чтений\n"
        "• Данные подписки\n\n"
        "Цели обработки:\n"
        "✅ Астрологические расчёты\n"
        "✅ Персонализированные прогнозы\n"
        "✅ Управление подпиской\n\n"
        "Мы НЕ передаём данные третьим лицам.\n"
        "Данные хранятся в зашифрованном виде.\n\n"
        "Ваши права (GDPR / ФЗ-152):\n"
        "/my_data — просмотр данных\n"
        "/export_data — экспорт в JSON\n"
        "/delete_data — полное удаление",
        parse_mode="HTML",
    )


@router.message(Command("my_data"))
async def cmd_my_data(message: Message):
    if not message.from_user:
        return
    data = await export_user_data(message.from_user.id)
    if not data:
        await message.answer("ℹ️ У нас нет ваших данных.")
        return

    text = json.dumps(data, ensure_ascii=False, indent=2)
    if len(text) > 4000:
        text = text[:4000] + "\n... (сокращено)"
    await message.answer(f"📊 <b>Ваши данные:</b>\n\n<pre>{text}</pre>", parse_mode="HTML")


@router.callback_query(F.data == "gdpr_my_data")
async def gdpr_my_data_cb(callback: CallbackQuery):
    data = await export_user_data(callback.from_user.id)
    if not data:
        await callback.answer("Данные не найдены", show_alert=True)
        return
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if len(text) > 4000:
        text = text[:4000] + "\n... (сокращено)"
    await callback.message.answer(f"📊 <b>Ваши данные:</b>\n\n<pre>{text}</pre>", parse_mode="HTML")
    await callback.answer()


@router.message(Command("export_data"))
async def cmd_export_data(message: Message):
    if not message.from_user:
        return
    data = await export_user_data(message.from_user.id)
    if not data:
        await message.answer("ℹ️ У нас нет ваших данных.")
        return

    from aiogram.types import BufferedInputFile
    json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    file = BufferedInputFile(json_bytes, filename=f"stellarium_data_{message.from_user.id}.json")
    await message.answer_document(file, caption="📦 Экспорт ваших данных (GDPR)")


@router.message(Command("delete_data"))
async def cmd_delete_data(message: Message):
    await message.answer(
        "⚠️ <b>Удаление аккаунта</b>\n\n"
        "Это действие удалит ВСЕ ваши данные:\n"
        "• Профиль и данные рождения\n"
        "• Историю чтений\n"
        "• Подписки\n\n"
        "Это действие <b>необратимо</b>. Вы уверены?",
        reply_markup=confirm_delete_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "gdpr_delete")
async def gdpr_delete_cb(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚠️ <b>Удаление аккаунта</b>\n\n"
        "Это действие удалит ВСЕ ваши данные безвозвратно.\nВы уверены?",
        reply_markup=confirm_delete_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "gdpr_delete_confirm")
async def gdpr_delete_confirm(callback: CallbackQuery):
    await delete_user_data(callback.from_user.id)
    await callback.message.edit_text(
        "✅ Все ваши данные удалены.\n\n"
        "Спасибо, что пользовались Stellarium AI. "
        "Вы всегда можете вернуться с /start",
    )
    await callback.answer()
