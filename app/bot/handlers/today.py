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


@router.message(Command("today"))
async def cmd_today(message: Message, session: AsyncSession) -> None:
    user, chart, _ = await _get_chart_for_user(session, message.from_user.id)
    if not chart:
        await message.answer("❌ Сначала создайте натальную карту.", reply_markup=start_keyboard())
        return

    await message.answer("☀️ Составляю персональный прогноз на сегодня...")
    transits = calculator.calculate_transits(chart)
    analysis = await ai.interpret_daily(chart, transits, message.from_user.first_name or "друг")
    await crud.save_reading(session, user.telegram_id, "daily", None, analysis)
    await message.answer(f"☀️ **Прогноз на сегодня**\n\n{analysis}", parse_mode="Markdown", reply_markup=main_menu_keyboard())


@router.message(Command("week"))
async def cmd_week(message: Message, session: AsyncSession) -> None:
    user = await crud.get_user(session, message.from_user.id)
    if not user or not user.birth_data:
        await message.answer("❌ Сначала создайте натальную карту.", reply_markup=start_keyboard())
        return

    if not crud.has_plan_access(user, "pro"):
        await message.answer(
            "🔒 Недельный прогноз доступен в подписке Stellarium Pro.\n\n"
            "Оформите подписку для доступа к расширенным прогнозам.",
            reply_markup=subscription_keyboard(),
        )
        return

    _, chart, _ = await _get_chart_for_user(session, message.from_user.id)
    await message.answer("📅 Составляю прогноз на неделю...")
    analysis = await ai.interpret_weekly(chart, message.from_user.first_name or "друг")
    await crud.save_reading(session, user.telegram_id, "weekly", None, analysis)
    await message.answer(f"📅 **Прогноз на неделю**\n\n{analysis}", parse_mode="Markdown", reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "cmd_today")
async def callback_today(callback: CallbackQuery, session: AsyncSession) -> None:
    user, chart, _ = await _get_chart_for_user(session, callback.from_user.id)
    if not chart:
        await callback.message.answer("❌ Сначала создайте натальную карту.", reply_markup=start_keyboard())
        await callback.answer()
        return

    await callback.message.answer("☀️ Составляю прогноз...")
    transits = calculator.calculate_transits(chart)
    analysis = await ai.interpret_daily(chart, transits, callback.from_user.first_name or "друг")
    await crud.save_reading(session, user.telegram_id, "daily", None, analysis)
    await callback.message.answer(f"☀️ Прогноз на сегодня\n\n{analysis}", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "cmd_week")
async def callback_week(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await crud.get_user(session, callback.from_user.id)
    if not user or not user.birth_data:
        await callback.message.answer("❌ Сначала создайте натальную карту.", reply_markup=start_keyboard())
        await callback.answer()
        return

    if not crud.has_plan_access(user, "pro"):
        await callback.message.answer(
            "🔒 Недельный прогноз — Premium функция.",
            reply_markup=subscription_keyboard(),
        )
        await callback.answer()
        return

    _, chart, _ = await _get_chart_for_user(session, callback.from_user.id)
    analysis = await ai.interpret_weekly(chart, callback.from_user.first_name or "друг")
    await crud.save_reading(session, user.telegram_id, "weekly", None, analysis)
    await callback.message.answer(f"📅 Прогноз на неделю\n\n{analysis}", reply_markup=main_menu_keyboard())
    await callback.answer()
