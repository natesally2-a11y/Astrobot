from __future__ import annotations

import json
from datetime import date

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.ai_interpreter import AIInterpreter, disclaimer_suffix
from app.astrology.calculations import build_natal_chart, calculate_transits
from app.astrology.chart_renderer import render_chart_svg
from app.astrology.schemas import BirthProfile
from app.bot.keyboards.common import (
    consent_keyboard,
    delete_confirmation_keyboard,
    settings_keyboard,
    start_keyboard,
    upgrade_keyboard,
)
from app.bot.states import AskAstrologer, Compatibility, Onboarding
from app.bot.utils.geocoding import geocode_place
from app.bot.utils.parsing import parse_birth_date, parse_birth_time
from app.bot.utils.profiles import birth_profile_from_user
from app.config import get_settings
from app.database import crud
from app.legal import ASTROLOGY_DISCLAIMER, GDPR_CONSENT_TEXT, PRIVACY_SHORT

router = Router(name="core")
interpreter = AIInterpreter()

WELCOME_TEXT = (
    "👋 Добро пожаловать в Stellarium AI!\n\n"
    "Я — ваш персональный ИИ-астролог. Создам точную натальную карту и буду давать прогнозы, "
    "основанные именно на вашей карте, а не на общих гороскопах.\n\n"
    "Для начала мне нужны данные рождения:\n"
    "📅 Дата рождения\n"
    "⏰ Время рождения (хотя бы примерное)\n"
    "📍 Место рождения (город)"
)

HELP_TEXT = (
    "/start — Приветствие и регистрация\n"
    "/chart — Показать натальную карту\n"
    "/today — Персональный прогноз на сегодня\n"
    "/week — Прогноз на неделю (Premium)\n"
    "/compatibility — Совместимость с партнером\n"
    "/ask — Задать вопрос астрологу\n"
    "/transit — Важные транзиты (Premium)\n"
    "/settings — Настройки и подписка\n"
    "/privacy — Политика конфиденциальности\n"
    "/my_data — Показать сохраненные данные\n"
    "/export_data — Экспорт данных в JSON\n"
    "/delete_data — Удалить аккаунт и данные\n"
    "/help — Справка по командам"
)

PLANS = {
    "pro": {
        "title": "Stellarium Pro — месячная подписка",
        "description": "Подробные прогнозы, совместимость до 3 партнеров и безлимитные вопросы ИИ.",
        "amount": 50,
        "label": "Stellarium Pro",
    },
    "oracle": {
        "title": "Космический Оракул — месячная подписка",
        "description": "Все из Pro плюс бизнес-астрология, годовые прогнозы и приоритетная поддержка ИИ.",
        "amount": 150,
        "label": "Космический Оракул",
    },
}


async def _require_profile(message: Message, session: AsyncSession):
    user = await crud.get_user_with_birth_data(session, message.from_user.id)
    if user is None or user.birth_data is None or not user.gdpr_consent:
        await message.answer("Сначала нужно создать натальную карту и принять согласие.", reply_markup=start_keyboard())
        return None
    return user


async def _send_natal_reading(message: Message, session: AsyncSession, user) -> None:
    chart = build_natal_chart(birth_profile_from_user(user))
    svg = render_chart_svg(chart).encode("utf-8")
    await message.answer_document(BufferedInputFile(svg, filename="stellarium_chart.svg"), caption="Ваша натальная карта")
    reading = await interpreter.natal_reading(chart)
    await crud.save_reading(session, user.telegram_id, "natal", reading)
    await message.answer(reading + disclaimer_suffix())


async def _export_user_data_to_message(message: Message, session: AsyncSession, user_id: int) -> None:
    data = await crud.export_user_data(session, user_id)
    if data is None:
        await message.answer("Данных пока нет. Запустите /start, чтобы создать профиль.")
        return
    payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    await message.answer_document(BufferedInputFile(payload, filename="stellarium_ai_export.json"))


@router.message(CommandStart())
async def start(message: Message, session: AsyncSession) -> None:
    await crud.get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
    )
    await message.answer(WELCOME_TEXT, reply_markup=start_keyboard())
    await message.answer(ASTROLOGY_DISCLAIMER)


@router.callback_query(F.data == "onboarding:start")
async def start_onboarding(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Onboarding.waiting_birth_date)
    await callback.message.answer(
        "Введите дату рождения в формате ДД.ММ.ГГГГ.\n"
        "Например: 24.08.1992\n\n"
        "В MVP дата вводится текстом; этот шаг готов для замены на расширенный inline-календарь."
    )
    await callback.answer()


@router.message(Onboarding.waiting_birth_date)
async def collect_birth_date(message: Message, state: FSMContext) -> None:
    try:
        birth_date = parse_birth_date(message.text or "")
    except ValueError:
        await message.answer("Не удалось распознать дату. Используйте формат ДД.ММ.ГГГГ, например 24.08.1992.")
        return
    await state.update_data(birth_date=birth_date.isoformat())
    await state.set_state(Onboarding.waiting_birth_time)
    await message.answer(
        "Введите время рождения в формате ЧЧ:ММ.\n"
        "Если точного времени нет, напишите «не знаю». Точность времени особенно важна для домов и асцендента."
    )


@router.message(Onboarding.waiting_birth_time)
async def collect_birth_time(message: Message, state: FSMContext) -> None:
    try:
        birth_time = parse_birth_time(message.text or "")
    except ValueError:
        await message.answer("Не удалось распознать время. Используйте ЧЧ:ММ или напишите «не знаю».")
        return
    await state.update_data(birth_time=birth_time.isoformat() if birth_time else None)
    await state.set_state(Onboarding.waiting_birth_place)
    await message.answer("Введите место рождения: город и, если нужно, страну. Например: Казань, Россия.")


@router.message(Onboarding.waiting_birth_place)
async def collect_birth_place(message: Message, state: FSMContext) -> None:
    try:
        place = await geocode_place(message.text or "")
    except ValueError:
        await message.answer("Введите название города.")
        return
    await state.update_data(
        birth_place=place.name,
        latitude=place.latitude,
        longitude=place.longitude,
        timezone=place.timezone,
    )
    await state.set_state(Onboarding.waiting_consent)
    await message.answer(f"Нашел место: {place.name}\n\n{GDPR_CONSENT_TEXT}", reply_markup=consent_keyboard())


@router.callback_query(F.data == "gdpr:agree")
async def accept_gdpr(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    await crud.get_or_create_user(
        session,
        telegram_id=callback.from_user.id,
        first_name=callback.from_user.first_name,
        username=callback.from_user.username,
    )
    await crud.set_gdpr_consent(session, callback.from_user.id, True)
    if {"birth_date", "birth_place"}.issubset(data.keys()):
        await crud.upsert_birth_data(
            session=session,
            user_id=callback.from_user.id,
            birth_date=date.fromisoformat(data["birth_date"]),
            birth_time=parse_birth_time(data["birth_time"]) if data.get("birth_time") else None,
            birth_place=data["birth_place"],
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            timezone_name=data.get("timezone"),
        )
        await state.clear()
        await callback.message.answer("Согласие сохранено. Создаю вашу первую натальную карту...")
        user = await crud.get_user_with_birth_data(session, callback.from_user.id)
        await _send_natal_reading(callback.message, session, user)
    else:
        await callback.message.answer("Согласие сохранено. Запустите /start, чтобы создать карту.")
    await callback.answer("Согласие принято")


@router.message(Command("chart"))
async def chart_command(message: Message, session: AsyncSession) -> None:
    user = await _require_profile(message, session)
    if user:
        await _send_natal_reading(message, session, user)


@router.message(Command("today"))
async def today_command(message: Message, session: AsyncSession) -> None:
    user = await _require_profile(message, session)
    if user is None:
        return
    chart = build_natal_chart(birth_profile_from_user(user))
    reading = await interpreter.daily_forecast(chart)
    await crud.save_reading(session, user.telegram_id, "daily", reading)
    await message.answer(reading + disclaimer_suffix())


@router.message(Command("week"))
async def week_command(message: Message, session: AsyncSession) -> None:
    user = await _require_profile(message, session)
    if user is None:
        return
    if not crud.has_active_paid_subscription(user):
        await message.answer("Недельные прогнозы доступны в Stellarium Pro и Космическом Оракуле.", reply_markup=upgrade_keyboard())
        return
    chart = build_natal_chart(birth_profile_from_user(user))
    reading = await interpreter.weekly_forecast(chart)
    await crud.save_reading(session, user.telegram_id, "weekly", reading)
    await message.answer(reading + disclaimer_suffix())


@router.message(Command("transit"))
async def transit_command(message: Message, session: AsyncSession) -> None:
    user = await _require_profile(message, session)
    if user is None:
        return
    if not crud.has_active_paid_subscription(user):
        await message.answer("Подробные транзиты доступны в Premium-подписке.", reply_markup=upgrade_keyboard())
        return
    chart = build_natal_chart(birth_profile_from_user(user))
    transits = calculate_transits(chart)
    if not transits:
        await message.answer("Сегодня нет точных сильных транзитов. Это хороший день для спокойной настройки.")
        return
    text = "Важные транзиты сегодня:\n" + "\n".join(
        f"• {item.transit_planet} {item.aspect} {item.natal_planet}, орб {item.orb}°" for item in transits
    )
    await message.answer(text + disclaimer_suffix())


@router.message(Command("ask"))
async def ask_command(message: Message, command: CommandObject, state: FSMContext, session: AsyncSession) -> None:
    user = await _require_profile(message, session)
    if user is None:
        return
    if not await crud.can_ask_ai(session, user):
        await message.answer("В бесплатном тарифе доступно 5 вопросов в день. Для безлимита подключите Pro.", reply_markup=upgrade_keyboard())
        return
    if command.args:
        chart = build_natal_chart(birth_profile_from_user(user))
        answer = await interpreter.answer_question(chart, command.args)
        await crud.save_reading(session, user.telegram_id, "ask", answer, question=command.args)
        await message.answer(answer + disclaimer_suffix())
        return
    await state.set_state(AskAstrologer.waiting_question)
    await message.answer("Напишите вопрос для ИИ-астролога одним сообщением.")


@router.message(AskAstrologer.waiting_question)
async def ask_question_message(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user = await _require_profile(message, session)
    if user is None:
        await state.clear()
        return
    if not await crud.can_ask_ai(session, user):
        await state.clear()
        await message.answer("Лимит free-вопросов на сегодня исчерпан. Для безлимита подключите Pro.", reply_markup=upgrade_keyboard())
        return
    question = message.text or ""
    chart = build_natal_chart(birth_profile_from_user(user))
    answer = await interpreter.answer_question(chart, question)
    await crud.save_reading(session, user.telegram_id, "ask", answer, question=question)
    await state.clear()
    await message.answer(answer + disclaimer_suffix())


@router.message(Command("compatibility"))
async def compatibility_command(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user = await _require_profile(message, session)
    if user is None:
        return
    await state.set_state(Compatibility.waiting_partner_date)
    await message.answer("Введите дату рождения партнера в формате ДД.ММ.ГГГГ.")


@router.message(Compatibility.waiting_partner_date)
async def collect_partner_date(message: Message, state: FSMContext) -> None:
    try:
        partner_date = parse_birth_date(message.text or "")
    except ValueError:
        await message.answer("Не удалось распознать дату. Используйте формат ДД.ММ.ГГГГ.")
        return
    await state.update_data(partner_date=partner_date.isoformat())
    await state.set_state(Compatibility.waiting_partner_time)
    await message.answer("Введите время рождения партнера в формате ЧЧ:ММ или «не знаю».")


@router.message(Compatibility.waiting_partner_time)
async def collect_partner_time(message: Message, state: FSMContext) -> None:
    try:
        partner_time = parse_birth_time(message.text or "")
    except ValueError:
        await message.answer("Не удалось распознать время. Используйте ЧЧ:ММ или «не знаю».")
        return
    await state.update_data(partner_time=partner_time.isoformat() if partner_time else None)
    await state.set_state(Compatibility.waiting_partner_place)
    await message.answer("Введите место рождения партнера.")


@router.message(Compatibility.waiting_partner_place)
async def collect_partner_place(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user = await _require_profile(message, session)
    if user is None:
        await state.clear()
        return
    place = await geocode_place(message.text or "")
    data = await state.get_data()
    partner_profile = BirthProfile(
        birth_date=date.fromisoformat(data["partner_date"]),
        birth_time=parse_birth_time(data["partner_time"]) if data.get("partner_time") else None,
        birth_place=place.name,
        latitude=place.latitude,
        longitude=place.longitude,
        timezone=place.timezone,
    )
    left = build_natal_chart(birth_profile_from_user(user))
    right = build_natal_chart(partner_profile)
    reading = await interpreter.compatibility(left, right)
    await crud.save_reading(session, user.telegram_id, "compatibility", reading, question=f"Партнер: {place.name}")
    await state.clear()
    await message.answer(reading + disclaimer_suffix())


@router.message(Command("settings"))
async def settings_command(message: Message, session: AsyncSession) -> None:
    user = await crud.get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
    )
    settings = get_settings()
    expires = user.subscription_expires_at.isoformat() if user.subscription_expires_at else "нет"
    text = (
        f"Текущий тариф: {user.subscription_type}\n"
        f"Действует до: {expires}\n\n"
        "Free: карта, краткий дневной прогноз и 5 вопросов в день.\n"
        "Pro: 50 Stars/месяц.\n"
        "Космический Оракул: 150 Stars/месяц."
    )
    await message.answer(text, reply_markup=settings_keyboard(settings.safe_webapp_url))


@router.message(Command("app"))
async def app_command(message: Message) -> None:
    settings = get_settings()
    await message.answer("Откройте Mini App для визуализации карты и настроек.", reply_markup=settings_keyboard(settings.safe_webapp_url))


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(f"{HELP_TEXT}\n\n{ASTROLOGY_DISCLAIMER}")


@router.message(Command("privacy"))
async def privacy_command(message: Message) -> None:
    await message.answer(PRIVACY_SHORT)


@router.callback_query(F.data == "privacy:show")
async def privacy_callback(callback: CallbackQuery) -> None:
    await callback.message.answer(PRIVACY_SHORT)
    await callback.answer()


@router.message(Command("my_data"))
async def my_data_command(message: Message, session: AsyncSession) -> None:
    data = await crud.export_user_data(session, message.from_user.id)
    if data is None:
        await message.answer("Данных пока нет.")
        return
    birth = data.get("birth_data") or {}
    await message.answer(
        "Ваши данные:\n"
        f"Telegram ID: {data['telegram_id']}\n"
        f"Имя: {data.get('first_name')}\n"
        f"Тариф: {data.get('subscription_type')}\n"
        f"Согласие GDPR/152-ФЗ: {data.get('gdpr_consent')}\n"
        f"Дата рождения: {birth.get('birth_date')}\n"
        f"Место рождения: {birth.get('birth_place')}\n"
        f"Чтений сохранено: {len(data.get('readings', []))}"
    )


@router.message(Command("export_data"))
async def export_data_command(message: Message, session: AsyncSession) -> None:
    await _export_user_data_to_message(message, session, message.from_user.id)


@router.callback_query(F.data == "data:export")
async def export_data_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    await _export_user_data_to_message(callback.message, session, callback.from_user.id)
    await callback.answer()


@router.message(Command("delete_data"))
async def delete_data_command(message: Message) -> None:
    await message.answer(
        "Удалить аккаунт, натальные данные, историю чтений и подписки? Это действие необратимо.",
        reply_markup=delete_confirmation_keyboard(),
    )


@router.callback_query(F.data == "data:delete_cancel")
async def delete_cancel(callback: CallbackQuery) -> None:
    await callback.message.answer("Удаление отменено.")
    await callback.answer()


@router.callback_query(F.data == "data:delete_confirm")
async def delete_confirm(callback: CallbackQuery, session: AsyncSession) -> None:
    deleted = await crud.delete_user_account(session, callback.from_user.id)
    await callback.message.answer("Все данные удалены." if deleted else "Данных для удаления не найдено.")
    await callback.answer()


@router.callback_query(F.data.startswith("subscribe:"))
async def subscribe_callback(callback: CallbackQuery, bot: Bot) -> None:
    plan = callback.data.split(":", 1)[1]
    plan_config = PLANS.get(plan)
    if plan_config is None:
        await callback.answer("Неизвестный тариф", show_alert=True)
        return
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=plan_config["title"],
        description=plan_config["description"],
        payload=f"subscription:{plan}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=plan_config["label"], amount=plan_config["amount"])],
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery) -> None:
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message, session: AsyncSession) -> None:
    payload = message.successful_payment.invoice_payload
    if not payload.startswith("subscription:"):
        await message.answer("Платеж получен, но тариф не распознан. Напишите в поддержку.")
        return
    plan = payload.split(":", 1)[1]
    plan_config = PLANS[plan]
    await crud.activate_subscription(session, message.from_user.id, plan, plan_config["amount"])
    await message.answer(f"Спасибо! Подписка {plan_config['label']} активирована на 30 дней.")


@router.inline_query()
async def inline_mode(inline_query: InlineQuery) -> None:
    query = (inline_query.query or "").strip()
    lower = query.lower()
    results: list[InlineQueryResultArticle] = []

    if lower.startswith("daily "):
        sign = query.split(maxsplit=1)[1].strip().title()
        text = (
            f"Сегодня для {sign}: ⭐ день подходит для наблюдения за внутренними сигналами, "
            "спокойных решений и одного практического шага к цели."
        )
        results.append(
            InlineQueryResultArticle(
                id=f"daily-{sign}",
                title=f"Прогноз на сегодня для {sign}",
                input_message_content=InputTextMessageContent(message_text=text),
            )
        )
    elif lower.startswith("compatibility "):
        parts = query.split()
        if len(parts) >= 3:
            first, second = parts[1].title(), parts[2].title()
            text = (
                f"Совместимость {first} и {second}: 🔥 союз раскрывается через честный диалог, "
                "уважение темпа друг друга и готовность видеть различия как ресурс."
            )
            results.append(
                InlineQueryResultArticle(
                    id=f"compat-{first}-{second}",
                    title=f"Совместимость {first} + {second}",
                    input_message_content=InputTextMessageContent(message_text=text),
                )
            )

    if not results:
        results = [
            InlineQueryResultArticle(
                id="example-daily",
                title="daily Virgo",
                input_message_content=InputTextMessageContent(
                    message_text="Сегодня для Virgo: ⭐ выберите один главный приоритет и действуйте спокойно."
                ),
            ),
            InlineQueryResultArticle(
                id="example-compatibility",
                title="compatibility Leo Scorpio",
                input_message_content=InputTextMessageContent(
                    message_text="Совместимость Leo и Scorpio: 🔥 сильное притяжение, которому нужны доверие и ясные границы."
                ),
            ),
        ]

    await inline_query.answer(results=results, cache_time=300, is_personal=False)
