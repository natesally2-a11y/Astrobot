from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology import AIInterpreter, ChartCalculator, ChartRenderer
from app.bot.keyboards.inline import main_menu_keyboard, start_keyboard
from app.bot.utils.geocoding import timezone_to_offset
from app.database import crud

router = Router()
calculator = ChartCalculator()
ai = AIInterpreter()
renderer = ChartRenderer()


async def _get_chart_for_user(session: AsyncSession, user_id: int):
    user = await crud.get_user(session, user_id)
    if not user or not user.birth_data:
        return None, None, None
    bd = user.birth_data
    tz_offset = timezone_to_offset(bd.timezone or "UTC+3")
    chart = calculator.calculate_natal_chart(
        bd.birth_date,
        bd.birth_time,
        float(bd.latitude),
        float(bd.longitude),
        tz_offset,
    )
    return user, chart, bd


@router.message(Command("chart"))
async def cmd_chart(message: Message, session: AsyncSession) -> None:
    user, chart, bd = await _get_chart_for_user(session, message.from_user.id)
    if not chart:
        await message.answer(
            "❌ Сначала создайте натальную карту.",
            reply_markup=start_keyboard(),
        )
        return

    await message.answer("🔮 Анализирую вашу натальную карту...")
    chart_text = calculator.chart_to_text(chart)
    analysis = await ai.interpret_natal(chart, message.from_user.first_name or "друг")
    await crud.save_reading(session, user.telegram_id, "natal", None, analysis)

    await message.answer(
        f"📊 **Натальная карта**\n"
        f"📍 {bd.birth_place}\n"
        f"📅 {bd.birth_date}"
        f"{f' ⏰ {bd.birth_time}' if bd.birth_time else ''}\n\n"
        f"```\n{chart_text}\n```",
        parse_mode="Markdown",
    )
    await message.answer(analysis, reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "cmd_chart")
async def callback_chart(callback: CallbackQuery, session: AsyncSession) -> None:
    user, chart, bd = await _get_chart_for_user(session, callback.from_user.id)
    if not chart:
        await callback.message.answer("❌ Сначала создайте натальную карту.", reply_markup=start_keyboard())
        await callback.answer()
        return

    await callback.message.answer("🔮 Анализирую вашу натальную карту...")
    analysis = await ai.interpret_natal(chart, callback.from_user.first_name or "друг")
    await crud.save_reading(session, user.telegram_id, "natal", None, analysis)
    chart_text = calculator.chart_to_text(chart)
    await callback.message.answer(
        f"📊 Натальная карта\n📍 {bd.birth_place}\n📅 {bd.birth_date}\n\n{chart_text}"
    )
    await callback.message.answer(analysis, reply_markup=main_menu_keyboard())
    await callback.answer()
