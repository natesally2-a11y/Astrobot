from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology import AIInterpreter, ChartCalculator
from app.bot.handlers.chart import _get_chart_for_user
from app.bot.keyboards.inline import main_menu_keyboard, start_keyboard, subscription_keyboard
from app.database import crud

router = Router()
calculator = ChartCalculator()
ai = AIInterpreter()


@router.message(Command("transit"))
async def cmd_transit(message: Message, session: AsyncSession) -> None:
    user = await crud.get_user(session, message.from_user.id)
    if not user or not user.birth_data:
        await message.answer("❌ Сначала создайте натальную карту.", reply_markup=start_keyboard())
        return

    if not crud.has_plan_access(user, "pro"):
        await message.answer(
            "🔒 Анализ транзитов доступен в Stellarium Pro.",
            reply_markup=subscription_keyboard(),
        )
        return

    _, chart, _ = await _get_chart_for_user(session, message.from_user.id)
    await message.answer("🌙 Анализирую текущие транзиты...")
    transits = calculator.calculate_transits(chart)
    analysis = await ai.interpret_transits(chart, transits, message.from_user.first_name or "друг")
    await crud.save_reading(session, user.telegram_id, "transit", None, analysis)
    await message.answer(f"🌙 **Важные транзиты**\n\n{analysis}", parse_mode="Markdown", reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "cmd_transit")
async def callback_transit(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await crud.get_user(session, callback.from_user.id)
    if not user or not user.birth_data:
        await callback.message.answer("❌ Сначала создайте натальную карту.", reply_markup=start_keyboard())
        await callback.answer()
        return

    if not crud.has_plan_access(user, "pro"):
        await callback.message.answer("🔒 Транзиты — Premium.", reply_markup=subscription_keyboard())
        await callback.answer()
        return

    _, chart, _ = await _get_chart_for_user(session, callback.from_user.id)
    transits = calculator.calculate_transits(chart)
    analysis = await ai.interpret_transits(chart, transits, callback.from_user.first_name or "друг")
    await crud.save_reading(session, user.telegram_id, "transit", None, analysis)
    await callback.message.answer(f"🌙 Транзиты\n\n{analysis}", reply_markup=main_menu_keyboard())
    await callback.answer()
