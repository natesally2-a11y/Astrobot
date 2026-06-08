from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.inline import city_keyboard, consent_keyboard, start_keyboard
from app.bot.states import Onboarding
from app.bot.utils.geocoding import search_cities
from app.bot.utils.parsing import parse_birth_date, parse_birth_time
from app.bot.utils.texts import ASTROLOGY_DISCLAIMER, GDPR_CONSENT_TEXT, PRIVACY_SUMMARY, WELCOME_TEXT
from app.database.crud import save_birth_data, save_gdpr_consent, upsert_user
from app.database.session import async_session

router = Router(name="onboarding")


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    referral_source_id = _parse_referral(message.text or "")
    user = message.from_user
    if user is None:
        return

    async with async_session() as session:
        await upsert_user(
            session=session,
            telegram_id=user.id,
            first_name=user.first_name,
            username=user.username,
            referral_source_id=referral_source_id,
        )

    await state.clear()
    await message.answer(f"{WELCOME_TEXT}\n{ASTROLOGY_DISCLAIMER}", reply_markup=start_keyboard())


@router.callback_query(F.data == "onboarding:start")
async def start_onboarding(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Onboarding.waiting_for_birth_date)
    await callback.message.answer("📅 Введите дату рождения в формате ДД.ММ.ГГГГ. Например: 24.03.1992")
    await callback.answer()


@router.message(Onboarding.waiting_for_birth_date)
async def receive_birth_date(message: Message, state: FSMContext) -> None:
    try:
        birth_date = parse_birth_date(message.text or "")
    except ValueError:
        await message.answer("Не получилось распознать дату. Введите в формате ДД.ММ.ГГГГ, например 24.03.1992.")
        return

    await state.update_data(birth_date=birth_date.isoformat())
    await state.set_state(Onboarding.waiting_for_birth_time)
    await message.answer(
        "⏰ Введите время рождения в формате ЧЧ:ММ.\n"
        "Если точного времени нет, напишите «не знаю» — я построю карту на 12:00, но дома будут менее точными."
    )


@router.message(Onboarding.waiting_for_birth_time)
async def receive_birth_time(message: Message, state: FSMContext) -> None:
    try:
        birth_time = parse_birth_time(message.text or "")
    except ValueError:
        await message.answer("Не получилось распознать время. Введите ЧЧ:ММ, например 08:45, или «не знаю».")
        return

    await state.update_data(birth_time=birth_time.isoformat() if birth_time else None)
    await state.set_state(Onboarding.waiting_for_birth_place)
    await message.answer("📍 Введите город рождения. Например: Москва, Санкт-Петербург, Алматы.")


@router.callback_query(F.data == "onboarding:place")
async def retry_place(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Onboarding.waiting_for_birth_place)
    await callback.message.answer("Введите город рождения еще раз.")
    await callback.answer()


@router.message(Onboarding.waiting_for_birth_place)
async def receive_birth_place(message: Message, state: FSMContext) -> None:
    query = (message.text or "").strip()
    if len(query) < 2:
        await message.answer("Введите хотя бы 2 символа названия города.")
        return

    try:
        cities = await search_cities(query)
    except Exception:
        await message.answer("Сервис геокодинга временно недоступен. Попробуйте еще раз или укажите город позже.")
        return

    if not cities:
        await message.answer("Город не найден. Попробуйте другое написание.")
        return

    await state.update_data(cities=cities)
    await state.set_state(Onboarding.waiting_for_city_choice)
    await message.answer("Выберите подходящий город:", reply_markup=city_keyboard(cities))


@router.callback_query(Onboarding.waiting_for_city_choice, F.data.startswith("city:"))
async def choose_city(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    cities = data.get("cities", [])
    try:
        city = cities[int((callback.data or "").split(":")[1])]
    except (IndexError, ValueError, TypeError):
        await callback.answer("Не удалось выбрать город, попробуйте еще раз.", show_alert=True)
        return

    await state.update_data(city=city)
    await state.set_state(Onboarding.waiting_for_consent)
    await callback.message.answer(GDPR_CONSENT_TEXT, reply_markup=consent_keyboard())
    await callback.answer()


@router.callback_query(F.data == "gdpr:accept")
async def accept_gdpr(callback: CallbackQuery, state: FSMContext) -> None:
    user = callback.from_user
    data = await state.get_data()
    city = data.get("city")
    if city is None or "birth_date" not in data:
        await callback.message.answer("Данные анкеты не найдены. Начните заново через /start.")
        await callback.answer()
        return

    async with async_session() as session:
        await save_gdpr_consent(session, user.id)
        await save_birth_data(
            session=session,
            user_id=user.id,
            birth_date=parse_birth_date(data["birth_date"]),
            birth_time=parse_birth_time(data["birth_time"]) if data.get("birth_time") else None,
            birth_place=str(city["place"]),
            latitude=float(city["latitude"]) if city.get("latitude") is not None else None,
            longitude=float(city["longitude"]) if city.get("longitude") is not None else None,
            timezone=str(city["timezone"]) if city.get("timezone") else None,
        )

    await state.clear()
    await callback.message.answer("✅ Натальная карта создана! Используйте /chart для анализа или /today для прогноза.")
    await callback.answer()


@router.callback_query(F.data == "legal:privacy")
async def show_privacy(callback: CallbackQuery) -> None:
    await callback.message.answer(PRIVACY_SUMMARY)
    await callback.answer()


def _parse_referral(text: str) -> int | None:
    parts = text.split(maxsplit=1)
    if len(parts) != 2 or not parts[1].startswith("ref_"):
        return None
    try:
        return int(parts[1].removeprefix("ref_"))
    except ValueError:
        return None
