from __future__ import annotations

from datetime import datetime

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.geocoding import search_places
from app.bot.keyboards.common import gdpr_keyboard, main_menu_keyboard, place_candidates_keyboard
from app.bot.states import OnboardingState
from app.bot.utils.texts import DISCLAIMER_TEXT, GDPR_CONSENT_TEXT, WELCOME_TEXT
from app.config import get_settings
from app.database import crud

router = Router(name=__name__)
settings = get_settings()


def _app_url_for_user(user_id: int) -> str | None:
    base = settings.webapp_base_url or settings.webhook_url
    if not base:
        return None
    return f"{base.rstrip('/')}/app?user_id={user_id}"


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user = message.from_user
    if user is None:
        return
    await crud.get_or_create_user(
        session=session,
        telegram_id=user.id,
        first_name=user.first_name,
        username=user.username,
    )
    await state.set_state(OnboardingState.waiting_birth_date)
    await message.answer(
        WELCOME_TEXT + "\n\n" + DISCLAIMER_TEXT + "\nВыберите дату рождения в календаре:",
        reply_markup=await SimpleCalendar(locale="ru_RU").start_calendar(),
    )


@router.callback_query(SimpleCalendarCallback.filter(), OnboardingState.waiting_birth_date)
async def process_birth_date(
    callback_query: CallbackQuery,
    callback_data: SimpleCalendarCallback,
    state: FSMContext,
) -> None:
    selected, selected_date = await SimpleCalendar(locale="ru_RU").process_selection(
        callback_query, callback_data
    )
    if not selected:
        return
    await state.update_data(birth_date=selected_date.isoformat())
    await state.set_state(OnboardingState.waiting_birth_time)
    await callback_query.message.answer(
        "⏰ Введите время рождения в формате HH:MM.\n"
        "Если не знаете точно, укажите примерное время — это лучше, чем пропуск."
    )


@router.message(OnboardingState.waiting_birth_time)
async def process_birth_time(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    try:
        birth_time = datetime.strptime(text, "%H:%M").time()
    except ValueError:
        await message.answer("Формат времени должен быть HH:MM, например 14:30.")
        return

    await state.update_data(birth_time=birth_time.strftime("%H:%M"))
    await state.set_state(OnboardingState.waiting_birth_place)
    await message.answer("📍 Введите место рождения (город), например: Москва")


@router.message(OnboardingState.waiting_birth_place)
async def process_birth_place(message: Message, state: FSMContext) -> None:
    query = (message.text or "").strip()
    if len(query) < 2:
        await message.answer("Введите корректное название города.")
        return
    places = await search_places(query, limit=3)
    if not places:
        await message.answer("Не удалось найти место. Попробуйте другое написание.")
        return
    await state.update_data(place_candidates=places)
    await message.answer("Выберите место рождения:", reply_markup=place_candidates_keyboard(places))


@router.callback_query(F.data.startswith("place_"), OnboardingState.waiting_birth_place)
async def choose_birth_place(callback_query: CallbackQuery, state: FSMContext) -> None:
    if callback_query.data == "place_retry":
        await callback_query.message.answer("Введите город заново.")
        return

    data = await state.get_data()
    candidates = data.get("place_candidates", [])
    idx = int(callback_query.data.split("_", maxsplit=1)[1])
    if idx >= len(candidates):
        await callback_query.answer("Выбранное место не найдено", show_alert=True)
        return

    selected = candidates[idx]
    await state.update_data(
        birth_place=selected["display_name"],
        latitude=selected["lat"],
        longitude=selected["lon"],
        timezone=selected.get("timezone"),
    )
    await state.set_state(OnboardingState.waiting_gdpr_consent)
    await callback_query.message.answer(GDPR_CONSENT_TEXT, reply_markup=gdpr_keyboard())


@router.callback_query(F.data == "show_privacy")
async def show_privacy_short(callback_query: CallbackQuery) -> None:
    await callback_query.message.answer(
        "Полная политика доступна в /privacy.\n"
        "Ключевой принцип: данные используются только для работы сервиса и могут быть удалены по /delete_data."
    )


@router.callback_query(F.data == "gdpr_agree", OnboardingState.waiting_gdpr_consent)
async def accept_gdpr(
    callback_query: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if callback_query.from_user is None:
        return

    data = await state.get_data()
    if not all(k in data for k in ("birth_date", "birth_time", "birth_place")):
        await callback_query.answer("Не хватает данных. Запустите /start снова.", show_alert=True)
        return

    birth_date = datetime.strptime(data["birth_date"], "%Y-%m-%d").date()
    birth_time = datetime.strptime(data["birth_time"], "%H:%M").time()
    await crud.set_gdpr_consent(session, callback_query.from_user.id, True)
    await crud.upsert_birth_data(
        session=session,
        user_id=callback_query.from_user.id,
        birth_date=birth_date,
        birth_time=birth_time,
        birth_place=data["birth_place"],
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        timezone=data.get("timezone"),
    )
    await state.clear()
    await callback_query.message.answer(
        "✅ Данные сохранены! Натальная карта готова.\n"
        "Используйте /chart для просмотра анализа.",
        reply_markup=main_menu_keyboard(_app_url_for_user(callback_query.from_user.id)),
    )
