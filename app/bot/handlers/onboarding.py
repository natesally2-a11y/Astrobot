"""Step-by-step birth-data collection."""
from __future__ import annotations

from datetime import date, datetime, time

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.calculations import timezone_for
from app.astrology.geocoding import geocode
from app.bot.keyboards import place_choice_kb, skip_time_kb, main_menu_kb
from app.bot.states import Onboarding
from app.database.crud import upsert_birth_data
from app.database.models import User

router = Router(name="onboarding")


@router.message(StateFilter(Onboarding.waiting_name), F.text)
async def take_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()[:80]
    await state.update_data(name=name)
    await message.answer(
        f"Приятно познакомиться, {name}! 🌟\n\n"
        "📅 Теперь укажите дату рождения в формате <code>ДД.ММ.ГГГГ</code>.\n"
        "Например: <code>14.02.1990</code>",
        parse_mode="HTML",
    )
    await state.set_state(Onboarding.waiting_date)


@router.message(StateFilter(Onboarding.waiting_date), F.text)
async def take_date(message: Message, state: FSMContext) -> None:
    raw = message.text.strip()
    parsed: date | None = None
    for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            parsed = datetime.strptime(raw, fmt).date()
            break
        except ValueError:
            continue
    if parsed is None or parsed.year < 1900 or parsed > date.today():
        await message.answer(
            "Не удалось распознать дату. Попробуйте формат ДД.ММ.ГГГГ, "
            "например 14.02.1990."
        )
        return

    await state.update_data(birth_date=parsed.isoformat())
    await message.answer(
        "⏰ Время рождения (формат <code>ЧЧ:ММ</code>, например <code>09:30</code>).\n"
        "Чем точнее — тем точнее карта.\n\n"
        "Если не знаете — нажмите кнопку ниже.",
        parse_mode="HTML",
        reply_markup=skip_time_kb(),
    )
    await state.set_state(Onboarding.waiting_time)


@router.callback_query(StateFilter(Onboarding.waiting_time), F.data == "birth:no_time")
async def skip_time(cq: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(birth_time=None, time_is_unknown=True)
    await cq.message.edit_reply_markup(reply_markup=None)
    await _ask_place(cq.message, state)
    await cq.answer()


@router.message(StateFilter(Onboarding.waiting_time), F.text)
async def take_time(message: Message, state: FSMContext) -> None:
    raw = message.text.strip().replace(".", ":").replace("-", ":")
    parsed: time | None = None
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            parsed = datetime.strptime(raw, fmt).time()
            break
        except ValueError:
            continue
    if parsed is None:
        await message.answer("Не понял время. Пример: 09:30")
        return
    await state.update_data(birth_time=parsed.isoformat(), time_is_unknown=False)
    await _ask_place(message, state)


async def _ask_place(message: Message, state: FSMContext) -> None:
    await message.answer(
        "📍 Город рождения. Напишите название (например, «Москва»)."
    )
    await state.set_state(Onboarding.waiting_place)


@router.message(StateFilter(Onboarding.waiting_place), F.text)
async def take_place(message: Message, state: FSMContext) -> None:
    query = message.text.strip()
    if not query:
        return
    await message.answer("🔍 Ищу город…")
    results = await geocode(query)
    if not results:
        await message.answer(
            "Не нашёл такой город. Попробуйте уточнить (например, «Москва, Россия»)."
        )
        return

    options_text = ["Выберите подходящий вариант:"]
    for idx, r in enumerate(results, 1):
        options_text.append(f"{idx}. {r.display_name}")
    await state.update_data(
        place_query=query,
        place_options=[
            {"name": r.display_name, "lat": r.latitude, "lon": r.longitude}
            for r in results
        ],
    )
    await message.answer("\n".join(options_text), reply_markup=place_choice_kb(results))
    await state.set_state(Onboarding.waiting_place_choice)


@router.callback_query(
    StateFilter(Onboarding.waiting_place_choice), F.data == "place:retry"
)
async def retry_place(cq: CallbackQuery, state: FSMContext) -> None:
    await cq.message.edit_reply_markup(reply_markup=None)
    await cq.message.answer("Введите название города ещё раз:")
    await state.set_state(Onboarding.waiting_place)
    await cq.answer()


@router.callback_query(
    StateFilter(Onboarding.waiting_place_choice), F.data.startswith("place:")
)
async def choose_place(
    cq: CallbackQuery, state: FSMContext, session: AsyncSession, user: User
) -> None:
    data = await state.get_data()
    options = data.get("place_options") or []
    try:
        idx = int(cq.data.split(":")[1])
        chosen = options[idx]
    except (ValueError, IndexError):
        await cq.answer("Не удалось выбрать вариант.", show_alert=True)
        return

    bt_str = data.get("birth_time")
    birth_time = time.fromisoformat(bt_str) if bt_str else None
    time_unknown = bool(data.get("time_is_unknown")) or birth_time is None
    birth_date = date.fromisoformat(data["birth_date"])
    tz_name = timezone_for(chosen["lat"], chosen["lon"])

    await upsert_birth_data(
        session,
        user_id=user.telegram_id,
        name=data.get("name"),
        birth_date=birth_date,
        birth_time=birth_time,
        time_is_unknown=time_unknown,
        birth_place=chosen["name"],
        latitude=chosen["lat"],
        longitude=chosen["lon"],
        timezone_name=tz_name,
    )

    await cq.message.edit_reply_markup(reply_markup=None)
    await cq.message.answer(
        "✨ Данные сохранены! Натальная карта готова к построению.\n\n"
        "Нажмите кнопку «🌟 Натальная карта» или используйте /chart, "
        "чтобы получить подробный разбор.",
        reply_markup=main_menu_kb(),
    )
    await state.clear()
    await cq.answer()
