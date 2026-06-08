"""Handler for /start command and onboarding flow."""

from datetime import date, time
from decimal import Decimal

from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.database.crud import (
    get_or_create_user,
    set_gdpr_consent,
    save_birth_data,
    update_user,
    grant_referral_bonus,
)
from app.bot.keyboards.inline import (
    start_keyboard,
    gdpr_consent_keyboard,
    birth_date_year_keyboard,
    birth_date_year_detail_keyboard,
    birth_month_keyboard,
    birth_day_keyboard,
    birth_time_keyboard,
    birth_time_minutes_keyboard,
)
from app.bot.utils.geocoding import geocode_city

router = Router()

WELCOME_TEXT = """👋 <b>Добро пожаловать в Stellarium AI!</b>

Я — ваш персональный ИИ-астролог. Создам точную натальную карту и буду давать прогнозы, основанные именно на <b>вашей карте</b>, а не на общих гороскопах.

Для начала мне нужны данные рождения:
📅 Дата рождения
⏰ Время рождения (хотя бы примерное)
📍 Место рождения (город)

⚠️ <i>Астрологические прогнозы носят исключительно развлекательный характер и не являются руководством к действию.</i>"""

GDPR_TEXT = """📋 <b>Согласие на обработку персональных данных</b>

Для создания персональной натальной карты нам необходимы:
• Дата, время и место рождения
• Имя для персонализации

Мы обрабатываем эти данные для:
✅ Астрологических расчётов
✅ Персонализированных прогнозов
✅ Работы подписки

Мы <b>НЕ</b> передаём данные третьим лицам.
Вы можете удалить все данные командой /delete_data

Согласие с условиями обработки данных в соответствии с ФЗ-152 «О персональных данных» и GDPR."""


class OnboardingStates(StatesGroup):
    waiting_city = State()
    waiting_exact_time = State()
    compat_city = State()
    compat_date = State()
    compat_time = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, command: CommandObject | None = None):
    if not message.from_user:
        return

    referrer_id = None
    if command and command.args and command.args.startswith("ref_"):
        try:
            referrer_id = int(command.args[4:])
        except ValueError:
            pass

    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
        language_code=message.from_user.language_code,
        referrer_id=referrer_id,
    )

    if referrer_id and referrer_id != message.from_user.id:
        await grant_referral_bonus(referrer_id)

    await state.clear()
    await message.answer(WELCOME_TEXT, reply_markup=start_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "onboard_start")
async def onboard_start(callback: CallbackQuery, state: FSMContext):
    user = await get_or_create_user(
        telegram_id=callback.from_user.id,
        first_name=callback.from_user.first_name,
        username=callback.from_user.username,
    )
    if not user.gdpr_consent:
        await callback.message.edit_text(GDPR_TEXT, reply_markup=gdpr_consent_keyboard(), parse_mode="HTML")
    else:
        await callback.message.edit_text(
            "📅 <b>Выберите десятилетие года рождения:</b>",
            reply_markup=birth_date_year_keyboard(),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data == "gdpr_accept")
async def gdpr_accept(callback: CallbackQuery, state: FSMContext):
    await set_gdpr_consent(callback.from_user.id)
    await callback.message.edit_text(
        "✅ Спасибо! Данные будут обработаны в соответствии с законодательством.\n\n"
        "📅 <b>Выберите десятилетие года рождения:</b>",
        reply_markup=birth_date_year_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "privacy_policy")
async def show_privacy(callback: CallbackQuery):
    await callback.message.answer(
        "📄 <b>Политика конфиденциальности</b>\n\n"
        "Stellarium AI обрабатывает данные рождения исключительно для "
        "астрологических расчётов. Данные хранятся в зашифрованном виде и "
        "не передаются третьим лицам.\n\n"
        "Ваши права:\n"
        "• /my_data — просмотр данных\n"
        "• /export_data — экспорт в JSON\n"
        "• /delete_data — полное удаление\n\n"
        "Контакт: через бота @stellarium_ai_bot",
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "about_bot")
async def about_bot(callback: CallbackQuery):
    await callback.message.edit_text(
        "🌟 <b>Stellarium AI</b> — первый астрологический бот, который даёт "
        "персонализированные прогнозы на основе точной натальной карты + "
        "текущих транзитов.\n\n"
        "В отличие от обычных гороскопов по знакам, мы рассчитываем вашу "
        "натальную карту с помощью Swiss Ephemeris и анализируем её с помощью ИИ.\n\n"
        "Команды:\n"
        "/chart — натальная карта\n"
        "/today — прогноз на сегодня\n"
        "/week — прогноз на неделю (Pro)\n"
        "/compatibility — совместимость\n"
        "/ask — вопрос астрологу\n"
        "/transit — анализ транзитов (Pro)\n"
        "/settings — настройки",
        reply_markup=start_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


# --- Year / Month / Day / Time selection ---

@router.callback_query(F.data.startswith("decade_"))
async def select_decade(callback: CallbackQuery, state: FSMContext):
    decade = int(callback.data.split("_")[1])
    await callback.message.edit_text(
        "📅 <b>Выберите год рождения:</b>",
        reply_markup=birth_date_year_detail_keyboard(decade),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("year_"))
async def select_year(callback: CallbackQuery, state: FSMContext):
    year = int(callback.data.split("_")[1])
    await state.update_data(birth_year=year)
    await callback.message.edit_text(
        f"📅 Год: <b>{year}</b>\n\nВыберите месяц рождения:",
        reply_markup=birth_month_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("month_"))
async def select_month(callback: CallbackQuery, state: FSMContext):
    month = int(callback.data.split("_")[1])
    data = await state.get_data()
    year = data.get("birth_year", 2000)
    await state.update_data(birth_month=month)
    months_ru = [
        "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
    ]
    await callback.message.edit_text(
        f"📅 {months_ru[month]} {year}\n\nВыберите день рождения:",
        reply_markup=birth_day_keyboard(month, year),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("day_"))
async def select_day(callback: CallbackQuery, state: FSMContext):
    day = int(callback.data.split("_")[1])
    await state.update_data(birth_day=day)
    await callback.message.edit_text(
        "⏰ <b>Выберите примерное время рождения:</b>\n\n"
        "Точное время важно для расчёта Асцендента и домов.\n"
        "Если не знаете — выберите «Не знаю время».",
        reply_markup=birth_time_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("hour_"))
async def select_hour(callback: CallbackQuery, state: FSMContext):
    hour = int(callback.data.split("_")[1])
    await callback.message.edit_text(
        f"⏰ Уточните время (≈ {hour:02d}:00):",
        reply_markup=birth_time_minutes_keyboard(hour),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("time_") & ~F.data.in_({"time_exact", "time_unknown"}))
async def select_time(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    hour = int(parts[1])
    minute = int(parts[2])
    await state.update_data(birth_hour=hour, birth_minute=minute)
    await callback.message.edit_text(
        f"⏰ Время: <b>{hour:02d}:{minute:02d}</b>\n\n"
        "📍 <b>Введите город рождения</b> (например: Москва, Киев, Минск):",
        parse_mode="HTML",
    )
    await state.set_state(OnboardingStates.waiting_city)
    await callback.answer()


@router.callback_query(F.data == "time_exact")
async def time_exact(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "⏰ Введите точное время рождения в формате <b>ЧЧ:ММ</b> (например: 14:35):",
        parse_mode="HTML",
    )
    await state.set_state(OnboardingStates.waiting_exact_time)
    await callback.answer()


@router.message(OnboardingStates.waiting_exact_time)
async def process_exact_time(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    try:
        parts = text.replace(".", ":").replace("-", ":").split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except (ValueError, IndexError):
        await message.answer("❌ Неверный формат. Введите время как <b>ЧЧ:ММ</b> (например: 14:35):", parse_mode="HTML")
        return

    await state.update_data(birth_hour=hour, birth_minute=minute)
    await message.answer(
        f"⏰ Время: <b>{hour:02d}:{minute:02d}</b>\n\n"
        "📍 <b>Введите город рождения</b> (например: Москва, Киев, Минск):",
        parse_mode="HTML",
    )
    await state.set_state(OnboardingStates.waiting_city)


@router.callback_query(F.data == "time_unknown")
async def time_unknown(callback: CallbackQuery, state: FSMContext):
    await state.update_data(birth_hour=12, birth_minute=0, time_unknown=True)
    await callback.message.edit_text(
        "ℹ️ Будем использовать полдень (12:00). Асцендент и дома будут приблизительными.\n\n"
        "📍 <b>Введите город рождения</b> (например: Москва, Киев, Минск):",
        parse_mode="HTML",
    )
    await state.set_state(OnboardingStates.waiting_city)
    await callback.answer()


@router.callback_query(F.data == "onboard_time")
async def back_to_time(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "⏰ <b>Выберите примерное время рождения:</b>",
        reply_markup=birth_time_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(OnboardingStates.waiting_city)
async def process_city(message: Message, state: FSMContext):
    city = message.text.strip() if message.text else ""
    if not city or len(city) < 2:
        await message.answer("❌ Введите название города (минимум 2 символа):")
        return

    await message.answer("🔍 Ищу город...")
    geo = await geocode_city(city)

    if not geo:
        await message.answer(
            "❌ Город не найден. Попробуйте ввести полное название на русском или английском:"
        )
        return

    data = await state.get_data()
    birth_year = data.get("birth_year", 2000)
    birth_month = data.get("birth_month", 1)
    birth_day = data.get("birth_day", 1)
    birth_hour = data.get("birth_hour", 12)
    birth_minute = data.get("birth_minute", 0)

    birth_date_val = date(birth_year, birth_month, birth_day)
    birth_time_val = time(birth_hour, birth_minute)

    await save_birth_data(
        user_id=message.from_user.id,
        birth_date=birth_date_val,
        birth_time=birth_time_val,
        birth_place=geo["display_name"],
        latitude=Decimal(str(geo["latitude"])),
        longitude=Decimal(str(geo["longitude"])),
        timezone=geo["timezone"],
    )

    await update_user(message.from_user.id, onboarding_step="completed")
    await state.clear()

    time_note = ""
    if data.get("time_unknown"):
        time_note = "\n⚠️ <i>Время неизвестно — используется 12:00</i>"

    await message.answer(
        f"✅ <b>Данные сохранены!</b>\n\n"
        f"📅 Дата: {birth_day:02d}.{birth_month:02d}.{birth_year}\n"
        f"⏰ Время: {birth_hour:02d}:{birth_minute:02d}{time_note}\n"
        f"📍 Место: {geo['display_name']}\n"
        f"🌐 Координаты: {geo['latitude']:.4f}, {geo['longitude']:.4f}\n\n"
        f"Теперь вы можете:\n"
        f"/chart — посмотреть натальную карту\n"
        f"/today — получить прогноз на сегодня\n"
        f"/ask — задать вопрос астрологу",
        parse_mode="HTML",
    )
