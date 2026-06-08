from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology import AIInterpreter, ChartCalculator
from app.bot.handlers.chart import _get_chart_for_user
from app.bot.keyboards.inline import main_menu_keyboard, start_keyboard, subscription_keyboard
from app.bot.states import CompatibilityStates
from app.bot.utils.geocoding import geocode_place, timezone_to_offset
from app.database import crud

router = Router()
calculator = ChartCalculator()
ai = AIInterpreter()


@router.message(Command("compatibility"))
async def cmd_compatibility(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user = await crud.get_user(session, message.from_user.id)
    if not user or not user.birth_data:
        await message.answer("❌ Сначала создайте натальную карту.", reply_markup=start_keyboard())
        return

    if not crud.has_plan_access(user, "pro"):
        partners = await crud.get_partners(session, user.telegram_id)
        if len(partners) >= 1:
            await message.answer(
                "🔒 Бесплатный план: 1 анализ совместимости.\n"
                "Оформите Pro для анализа до 3 партнёров.",
                reply_markup=subscription_keyboard(),
            )
            return

    await state.set_state(CompatibilityStates.waiting_partner_name)
    await message.answer("💕 Введите имя партнёра:")


@router.callback_query(F.data == "cmd_compatibility")
async def callback_compatibility(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    user = await crud.get_user(session, callback.from_user.id)
    if not user or not user.birth_data:
        await callback.message.answer("❌ Сначала создайте натальную карту.", reply_markup=start_keyboard())
        await callback.answer()
        return

    await state.set_state(CompatibilityStates.waiting_partner_name)
    await callback.message.answer("💕 Введите имя партнёра:")
    await callback.answer()


@router.message(CompatibilityStates.waiting_partner_name)
async def partner_name(message: Message, state: FSMContext) -> None:
    await state.update_data(partner_name=message.text.strip())
    await state.set_state(CompatibilityStates.waiting_partner_date)
    await message.answer("📅 Введите дату рождения партнёра (ДД.ММ.ГГГГ):")


@router.message(CompatibilityStates.waiting_partner_date)
async def partner_date(message: Message, state: FSMContext) -> None:
    try:
        parts = message.text.strip().split(".")
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
        from datetime import date
        birth_date = date(year, month, day)
    except (ValueError, IndexError):
        await message.answer("❌ Неверный формат. Введите дату как ДД.ММ.ГГГГ:")
        return
    await state.update_data(partner_birth_date=birth_date)
    await state.set_state(CompatibilityStates.waiting_partner_place)
    await message.answer("📍 Введите город рождения партнёра:")


@router.message(CompatibilityStates.waiting_partner_place)
async def partner_place(message: Message, state: FSMContext, session: AsyncSession) -> None:
    geo = await geocode_place(message.text.strip())
    if not geo:
        await message.answer("❌ Город не найден. Попробуйте снова:")
        return

    data = await state.get_data()
    user, chart1, _ = await _get_chart_for_user(session, message.from_user.id)
    if not chart1:
        await message.answer("❌ Сначала создайте свою карту.")
        await state.clear()
        return

    tz_offset = timezone_to_offset(geo.get("timezone", "UTC+3") if isinstance(geo, dict) else "UTC+3")
    from app.bot.utils.geocoding import estimate_timezone
    tz = estimate_timezone(geo["longitude"])
    tz_offset = timezone_to_offset(tz)

    chart2 = calculator.calculate_natal_chart(
        data["partner_birth_date"],
        None,
        geo["latitude"],
        geo["longitude"],
        tz_offset,
    )

    await message.answer("💕 Анализирую совместимость...")
    analysis = await ai.interpret_compatibility(
        chart1, chart2,
        message.from_user.first_name or "Вы",
        data["partner_name"],
    )
    await crud.save_partner(
        session,
        user.telegram_id,
        data["partner_name"],
        data["partner_birth_date"],
        None,
        geo["short_name"],
        geo["latitude"],
        geo["longitude"],
        tz,
    )
    await crud.save_reading(session, user.telegram_id, "compatibility", data["partner_name"], analysis)
    await state.clear()
    await message.answer(
        f"💕 Совместимость с {data['partner_name']}\n\n{analysis}",
        reply_markup=main_menu_keyboard(),
    )
