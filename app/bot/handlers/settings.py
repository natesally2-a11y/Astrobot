from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.inline import (
    confirm_delete_keyboard,
    main_menu_keyboard,
    settings_keyboard,
    subscription_keyboard,
)
from app.database import crud

router = Router()

PLAN_NAMES = {
    "free": "🆓 Бесплатный",
    "pro": "⭐ Stellarium Pro",
    "oracle": "🌌 Космический Оракул",
}


@router.message(Command("settings"))
async def cmd_settings(message: Message, session: AsyncSession) -> None:
    user = await crud.get_user(session, message.from_user.id)
    plan = crud.get_effective_plan(user) if user else "free"
    expires = ""
    if user and user.subscription_expires_at and crud.is_subscription_active(user):
        expires = f"\n📅 Действует до: {user.subscription_expires_at.strftime('%d.%m.%Y')}"

    await message.answer(
        f"⚙️ **Настройки**\n\n"
        f"Тариф: {PLAN_NAMES.get(plan, plan)}{expires}\n\n"
        f"Реферальная ссылка:\n"
        f"`t.me/{(await message.bot.get_me()).username}?start=ref_{message.from_user.id}`\n"
        f"Бонус: +1 неделя Pro за каждого друга",
        parse_mode="Markdown",
        reply_markup=settings_keyboard(),
    )


@router.callback_query(F.data == "cmd_settings")
@router.callback_query(F.data == "back_to_menu")
async def callback_settings(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await crud.get_user(session, callback.from_user.id)
    plan = crud.get_effective_plan(user) if user else "free"
    await callback.message.answer(
        f"⚙️ Настройки\nТариф: {PLAN_NAMES.get(plan, plan)}",
        reply_markup=settings_keyboard() if callback.data == "cmd_settings" else main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "show_subscription")
async def show_subscription(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await crud.get_user(session, callback.from_user.id)
    plan = crud.get_effective_plan(user) if user else "free"
    text = f"""💎 **Тарифные планы**

Ваш тариф: {PLAN_NAMES.get(plan, plan)}

🆓 **Бесплатный**
• Натальная карта + базовый анализ
• Краткий ежедневный прогноз
• 5 вопросов ИИ в день

⭐ **Stellarium Pro** (~50 Stars/мес)
• Подробные прогнозы
• Недельные прогнозы
• Совместимость (до 3 партнёров)
• Безлимитные вопросы
• Уведомления о транзитах

🌌 **Космический Оракул** (~150 Stars/мес)
• Всё из Pro +
• Бизнес-астрология
• Годовые прогнозы
• Индивидуальные рекомендации
• Приоритетная поддержка ИИ"""
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=subscription_keyboard())
    await callback.answer()


@router.callback_query(F.data == "my_data")
async def callback_my_data(callback: CallbackQuery, session: AsyncSession) -> None:
    data = await crud.export_user_data(session, callback.from_user.id)
    if not data:
        await callback.answer("Данные не найдены")
        return
    bd = data.get("birth_data")
    text = "📋 **Ваши данные**\n\n"
    if bd:
        text += f"📅 Дата: {bd['birth_date']}\n"
        text += f"⏰ Время: {bd.get('birth_time', 'не указано')}\n"
        text += f"📍 Место: {bd['birth_place']}\n"
    text += f"💎 Тариф: {data['user']['subscription_type']}\n"
    text += f"✅ GDPR: {'да' if data['user']['gdpr_consent'] else 'нет'}"
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()
