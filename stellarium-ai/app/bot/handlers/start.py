"""
/start command handler — Registration flow with GDPR consent.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError
import pytz

from app.bot.keyboards.inline import (
    get_gdpr_keyboard, get_year_keyboard, get_month_keyboard,
    get_day_keyboard, get_birth_time_keyboard, get_main_menu_keyboard,
    MonthCD, DayCD, YearCD, TimeCD,
)
from app.bot.states import RegistrationStates
from app.database import crud
from app.database.models import User
from app.config import settings

router = Router(name="start")

WELCOME_TEXT = """🌟 <b>Добро пожаловать в Stellarium AI!</b>

Я — ваш персональный ИИ-астролог. Создам точную натальную карту и буду давать прогнозы, основанные именно на вашей карте, а не на общих гороскопах.

Для начала мне нужны данные рождения:
📅 Дата рождения
⏰ Время рождения
📍 Место рождения

⭐ <b>Тарифы:</b>
• Бесплатно — карта + 5 вопросов в день
• Pro (50⭐/мес) — полные прогнозы + безлимит
• Оракул (150⭐/мес) — всё Pro + бизнес-астрология

Нажмите <b>«Начать»</b> для создания карты 👇"""

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

⚠️ <i>Астрологические прогнозы носят исключительно развлекательный характер.</i>

Для продолжения нажмите «Согласен»."""

DISCLAIMER = """⚠️ <b>Важно:</b> Астрологические прогнозы носят исключительно развлекательный характер и не являются руководством к действию.

Не используйте астрологию для принятия важных жизненных, медицинских или финансовых решений. При серьёзных проблемах обращайтесь к квалифицированным специалистам.

<i>Stellarium AI создан для саморазвития и развлечения.</i>"""


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db_user: Optional[User] = None, session=None):
    await state.clear()

    args = message.text.split()
    referral_id = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referral_id = int(args[1][4:])
        except ValueError:
            pass

    if referral_id and session and db_user:
        if db_user.referred_by is None and referral_id != message.from_user.id:
            await crud.add_referral_bonus(session, referral_id)

    if db_user and db_user.gdpr_consent:
        birth_data = await crud.get_birth_data(session, message.from_user.id)
        if birth_data:
            await message.answer(
                f"✨ С возвращением, <b>{message.from_user.first_name}</b>!\n\n"
                f"Ваша карта уже создана. Используйте меню для прогнозов:",
                parse_mode="HTML",
                reply_markup=get_main_menu_keyboard(
                    has_birth_data=True,
                    is_pro=db_user.is_pro,
                ),
            )
            return

    await message.answer(WELCOME_TEXT, parse_mode="HTML")
    await message.answer(GDPR_TEXT, parse_mode="HTML", reply_markup=get_gdpr_keyboard())
    await state.set_state(RegistrationStates.waiting_for_gdpr)


@router.callback_query(F.data == "gdpr:policy")
async def show_privacy_policy(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "📋 <b>Политика конфиденциальности</b>\n\n"
        "Полный текст доступен по команде /privacy\n\n"
        "Краткая версия:\n"
        "• Данные хранятся в защищённой базе данных\n"
        "• Не передаются третьим лицам\n"
        "• Вы можете удалить их в любой момент (/delete_data)",
        parse_mode="HTML",
    )


@router.callback_query(F.data == "gdpr:agree", RegistrationStates.waiting_for_gdpr)
async def gdpr_agreed(callback: CallbackQuery, state: FSMContext, session=None):
    await callback.answer("✅ Спасибо за согласие!")
    if session:
        await crud.update_gdpr_consent(session, callback.from_user.id)

    await callback.message.answer(
        "🎉 Отлично! Начнём создание вашей натальной карты.\n\n"
        "📅 <b>Шаг 1/3: Год рождения</b>\n\nВыберите год:",
        parse_mode="HTML",
        reply_markup=get_year_keyboard(),
    )
    await state.set_state(RegistrationStates.waiting_for_birth_year)


@router.callback_query(YearCD.filter(), RegistrationStates.waiting_for_birth_year)
async def process_year(callback: CallbackQuery, callback_data: YearCD, state: FSMContext):
    await state.update_data(year=callback_data.year)
    await callback.answer(f"Год: {callback_data.year}")
    await callback.message.edit_text(
        f"📅 Год: <b>{callback_data.year}</b> ✓\n\n"
        f"📅 <b>Шаг 1/3: Месяц рождения</b>\n\nВыберите месяц:",
        parse_mode="HTML",
        reply_markup=get_month_keyboard(),
    )
    await state.set_state(RegistrationStates.waiting_for_birth_month)


@router.callback_query(MonthCD.filter(), RegistrationStates.waiting_for_birth_month)
async def process_month(callback: CallbackQuery, callback_data: MonthCD, state: FSMContext):
    MONTHS = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
              "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
    await state.update_data(month=callback_data.month)
    await callback.answer(f"Месяц: {MONTHS[callback_data.month - 1]}")
    await callback.message.edit_text(
        f"📅 Месяц: <b>{MONTHS[callback_data.month - 1]}</b> ✓\n\n"
        f"📅 <b>Шаг 1/3: День рождения</b>\n\nВыберите день:",
        parse_mode="HTML",
        reply_markup=get_day_keyboard(callback_data.month),
    )
    await state.set_state(RegistrationStates.waiting_for_birth_day)


@router.callback_query(DayCD.filter(), RegistrationStates.waiting_for_birth_day)
async def process_day(callback: CallbackQuery, callback_data: DayCD, state: FSMContext):
    data = await state.get_data()
    year = data.get("year", 2000)
    await state.update_data(day=callback_data.day)
    await callback.answer(f"День: {callback_data.day}")

    try:
        birth_date = date(year, callback_data.month, callback_data.day)
        await state.update_data(birth_date=birth_date.isoformat())
    except ValueError:
        await callback.message.answer("❌ Некорректная дата. Попробуйте ещё раз.")
        return

    await callback.message.edit_text(
        f"📅 Дата рождения: <b>{callback_data.day:02d}.{callback_data.month:02d}.{year}</b> ✓\n\n"
        "⏰ <b>Шаг 2/3: Время рождения</b>\n\n"
        "Выберите примерное время рождения.\n"
        "<i>Точное время важно для расчёта асцендента и домов.</i>",
        parse_mode="HTML",
        reply_markup=get_birth_time_keyboard(),
    )
    await state.set_state(RegistrationStates.waiting_for_birth_time)


@router.callback_query(TimeCD.filter(), RegistrationStates.waiting_for_birth_time)
async def process_time(callback: CallbackQuery, callback_data: TimeCD, state: FSMContext):
    time_value = callback_data.value
    time_display = "Не указано" if time_value == "unknown" else time_value
    await state.update_data(birth_time=time_value)
    await callback.answer(f"Время: {time_display}")

    await callback.message.edit_text(
        f"⏰ Время рождения: <b>{time_display}</b> ✓\n\n"
        "📍 <b>Шаг 3/3: Место рождения</b>\n\n"
        "Введите город рождения (на русском или английском):\n\n"
        "<i>Например: Москва, Санкт-Петербург, Новосибирск</i>",
        parse_mode="HTML",
    )
    await state.set_state(RegistrationStates.waiting_for_birth_place)


@router.message(RegistrationStates.waiting_for_birth_place)
async def process_place(message: Message, state: FSMContext, session=None):
    place_name = message.text.strip()
    if len(place_name) < 2:
        await message.answer("❌ Введите название города.")
        return

    await message.answer("🔍 Ищу координаты города...")

    lat, lon, tz, full_place = await _geocode_place(place_name)

    if lat is None:
        await message.answer(
            f"❌ Не удалось найти город <b>{place_name}</b>.\n"
            "Попробуйте ввести по-другому (на английском или другое написание).",
            parse_mode="HTML",
        )
        return

    data = await state.get_data()
    birth_date_str = data.get("birth_date")
    birth_time_str = data.get("birth_time", "unknown")

    birth_date = date.fromisoformat(birth_date_str)
    birth_time_obj = None
    if birth_time_str != "unknown":
        try:
            h, m = map(int, birth_time_str.split(":"))
            birth_time_obj = datetime(2000, 1, 1, h, m)
        except Exception:
            pass

    await crud.save_birth_data(
        session,
        user_id=message.from_user.id,
        birth_date=birth_date,
        birth_time=birth_time_obj,
        birth_place=full_place or place_name,
        latitude=lat,
        longitude=lon,
        timezone=tz,
    )

    await state.clear()

    user = await crud.get_user(session, message.from_user.id)

    await message.answer(
        f"✅ <b>Данные сохранены!</b>\n\n"
        f"📅 Дата: {birth_date.strftime('%d.%m.%Y')}\n"
        f"⏰ Время: {birth_time_str if birth_time_str != 'unknown' else 'Не указано'}\n"
        f"📍 Место: {full_place or place_name}\n\n"
        f"🌟 Ваша натальная карта создана! Используйте /chart для просмотра.",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(has_birth_data=True, is_pro=user.is_pro if user else False),
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = """📖 <b>Команды Stellarium AI</b>

/start — Приветствие и регистрация
/chart — Показать натальную карту
/today — Персональный прогноз на сегодня
/week — Прогноз на неделю (Pro)
/compatibility — Совместимость с партнёром
/ask — Задать вопрос астрологу
/transit — Важные транзиты (Pro)
/settings — Настройки и подписка
/privacy — Политика конфиденциальности
/my_data — Мои сохранённые данные
/delete_data — Удалить все данные
/export_data — Экспорт данных (JSON)

""" + DISCLAIMER
    await message.answer(help_text, parse_mode="HTML")


@router.callback_query(F.data.startswith("menu:"))
async def handle_menu(callback: CallbackQuery, state: FSMContext, session=None):
    action = callback.data.split(":")[1]
    await callback.answer()

    if action == "chart":
        from app.bot.handlers.chart import send_chart
        await send_chart(callback.message, session, callback.from_user.id)
    elif action == "today":
        from app.bot.handlers.today import send_today
        await send_today(callback.message, session, callback.from_user.id)
    elif action == "week":
        from app.bot.handlers.week import send_week
        await send_week(callback.message, session, callback.from_user.id)
    elif action == "transit":
        from app.bot.handlers.transit import send_transit
        await send_transit(callback.message, session, callback.from_user.id)
    elif action == "compatibility":
        from app.bot.handlers.compatibility import start_compatibility
        await start_compatibility(callback.message, state)
    elif action == "ask":
        from app.bot.handlers.ask import start_ask
        await start_ask(callback.message, state)
    elif action in ("upgrade_pro", "upgrade_oracle"):
        from app.bot.handlers.payments import send_invoice_for_plan
        plan = "pro" if action == "upgrade_pro" else "oracle"
        await send_invoice_for_plan(callback.message, plan)
    elif action == "settings":
        from app.bot.handlers.settings import cmd_settings
        await cmd_settings(callback.message, session, callback.from_user.id)


async def _geocode_place(place_name: str) -> tuple:
    try:
        geolocator = Nominatim(user_agent="stellarium-ai-bot/1.0")
        location = geolocator.geocode(place_name, language="ru", timeout=10)
        if location is None:
            return None, None, "UTC", None

        lat = location.latitude
        lon = location.longitude

        tz = _estimate_timezone(lat, lon)
        return lat, lon, tz, location.address.split(",")[0]
    except GeocoderServiceError:
        return None, None, "UTC", None
    except Exception:
        return None, None, "UTC", None


def _estimate_timezone(lat: float, lon: float) -> str:
    try:
        from geopy.geocoders import Nominatim
        offset_hours = round(lon / 15)
        offset_hours = max(-12, min(12, offset_hours))
        if offset_hours == 0:
            return "UTC"
        if offset_hours > 0:
            return f"Etc/GMT-{offset_hours}"
        return f"Etc/GMT+{abs(offset_hours)}"
    except Exception:
        return "Europe/Moscow"
