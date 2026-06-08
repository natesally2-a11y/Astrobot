from __future__ import annotations

import json

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    BufferedInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
    WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.astrology.ai_interpreter import (
    answer_personal_question,
    interpret_daily_forecast,
    interpret_natal_chart,
    interpret_transits,
    interpret_weekly_forecast,
)
from app.astrology.calculations import calculate_natal_chart, sign_forecast
from app.astrology.chart_renderer import render_chart_svg
from app.bot.keyboards.onboarding import start_keyboard
from app.bot.keyboards.subscriptions import delete_data_keyboard
from app.bot.states import AskState
from app.bot.utils.formatters import (
    help_text,
    premium_gate_text,
    refund_policy_text,
    subscription_short_label,
    welcome_text,
)
from app.config import DISCLAIMER_TEXT, get_settings
from app.database.crud import (
    add_subscription,
    count_daily_questions,
    create_or_update_user,
    create_reading,
    delete_user_data,
    export_user_bundle,
    get_user,
)
from app.database.models import BirthData
from app.database.session import AsyncSessionLocal
from app.services.subscriptions import ORACLE_PLAN, PRO_PLAN, can_ask_question, plan_summary_text, resolve_user_tier


router = Router(name="general")
settings = get_settings()


def build_settings_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if settings.base_url:
        builder.row(
            InlineKeyboardButton(
                text="Открыть Mini App",
                web_app=WebAppInfo(url=f"{settings.base_url.rstrip('/')}/app"),
            )
        )
    builder.row(InlineKeyboardButton(text="Stellarium Pro", callback_data="buy:pro"))
    builder.row(InlineKeyboardButton(text="Cosmic Oracle", callback_data="buy:oracle"))
    return builder.as_markup()


async def _load_chart(telegram_id: int):
    async with AsyncSessionLocal() as session:
        birth_data = await session.get(BirthData, telegram_id)
        if birth_data is None:
            return None
        return calculate_natal_chart(
            birth_date=birth_data.birth_date,
            birth_time=birth_data.birth_time,
            birth_place=birth_data.birth_place,
            latitude=birth_data.latitude,
            longitude=birth_data.longitude,
            timezone_name=birth_data.timezone,
        )


def _svg_input(svg: str, telegram_id: int) -> BufferedInputFile:
    return BufferedInputFile(
        file=svg.encode("utf-8"),
        filename=f"stellarium-chart-{telegram_id}.svg",
    )


@router.message(Command("start"))
async def handle_start(message: Message, command: CommandObject | None) -> None:
    if message.from_user is None:
        return

    referred_by = None
    if command and command.args and command.args.startswith("ref_"):
        ref_value = command.args.removeprefix("ref_")
        referred_by = int(ref_value) if ref_value.isdigit() else None

    async with AsyncSessionLocal() as session:
        await create_or_update_user(
            session=session,
            telegram_id=message.from_user.id,
            first_name=message.from_user.first_name,
            username=message.from_user.username,
            referred_by=referred_by,
        )

    await message.answer(
        f"{welcome_text(message.from_user.first_name)}\n\n{DISCLAIMER_TEXT}",
        reply_markup=start_keyboard(),
    )


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    await message.answer(f"{help_text()}\n\n{DISCLAIMER_TEXT}")


@router.message(Command("privacy"))
async def handle_privacy(message: Message) -> None:
    text = (
        "Политика конфиденциальности: мы храним только данные, нужные для "
        "астрологических расчетов и работы подписки. Вы можете запросить /my_data, "
        "/export_data или /delete_data в любой момент.\n\n"
        "Полный текст политики и договоров доступен в документации проекта."
    )
    await message.answer(text)


@router.callback_query(F.data == "legal:privacy")
async def handle_privacy_callback(callback) -> None:
    await callback.message.answer(
        "Политика конфиденциальности: данные рождения используются только для "
        "создания карты, прогнозов и подписки. Команды для управления данными: "
        "/my_data, /export_data, /delete_data."
    )
    await callback.answer()


@router.message(Command("settings"))
async def handle_settings(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        user = await get_user(session, message.from_user.id if message.from_user else 0)
        current_plan = await resolve_user_tier(session, user)

    text = (
        f"Текущий тариф: {subscription_short_label(current_plan)}\n\n"
        f"{plan_summary_text(current_plan)}\n\n"
        f"{refund_policy_text()}"
    )
    await message.answer(text, reply_markup=build_settings_keyboard())


@router.message(Command("chart"))
async def handle_chart(message: Message) -> None:
    if message.from_user is None:
        return

    chart = await _load_chart(message.from_user.id)
    if chart is None:
        await message.answer(
            "Сначала создайте карту через /start и заполните дату, время и место рождения."
        )
        return

    svg = render_chart_svg(chart)
    interpretation = await interpret_natal_chart(chart)
    await message.answer_document(
        _svg_input(svg, message.from_user.id),
        caption=interpretation[:1024],
    )

    async with AsyncSessionLocal() as session:
        await create_reading(
            session,
            telegram_id=message.from_user.id,
            reading_type="natal",
            ai_response=interpretation,
        )


@router.message(Command("today"))
async def handle_today(message: Message) -> None:
    if message.from_user is None:
        return

    chart = await _load_chart(message.from_user.id)
    if chart is None:
        await message.answer("Сначала создайте натальную карту через /start.")
        return

    forecast = await interpret_daily_forecast(chart)
    await message.answer(forecast)
    async with AsyncSessionLocal() as session:
        await create_reading(session, message.from_user.id, "daily", forecast)


@router.message(Command("week"))
async def handle_week(message: Message) -> None:
    if message.from_user is None:
        return

    async with AsyncSessionLocal() as session:
        user = await get_user(session, message.from_user.id)
        tier = await resolve_user_tier(session, user)
    if tier not in {PRO_PLAN.code, ORACLE_PLAN.code}:
        await message.answer(premium_gate_text(), reply_markup=build_settings_keyboard())
        return

    chart = await _load_chart(message.from_user.id)
    if chart is None:
        await message.answer("Сначала создайте натальную карту через /start.")
        return

    forecast = await interpret_weekly_forecast(chart)
    await message.answer(forecast)
    async with AsyncSessionLocal() as session:
        await create_reading(session, message.from_user.id, "weekly", forecast)


@router.message(Command("transit"))
async def handle_transit(message: Message) -> None:
    if message.from_user is None:
        return

    async with AsyncSessionLocal() as session:
        user = await get_user(session, message.from_user.id)
        tier = await resolve_user_tier(session, user)
    if tier not in {PRO_PLAN.code, ORACLE_PLAN.code}:
        await message.answer(premium_gate_text(), reply_markup=build_settings_keyboard())
        return

    chart = await _load_chart(message.from_user.id)
    if chart is None:
        await message.answer("Сначала создайте натальную карту через /start.")
        return

    interpretation = await interpret_transits(chart)
    await message.answer(interpretation)
    async with AsyncSessionLocal() as session:
        await create_reading(session, message.from_user.id, "transits", interpretation)


@router.message(Command("ask"))
async def handle_ask(message: Message, state, command: CommandObject | None) -> None:
    if message.from_user is None:
        return

    question = command.args.strip() if command and command.args else ""
    if question:
        await _answer_question(message, question)
        return

    await state.set_state(AskState.waiting_for_question)
    await message.answer("Напишите ваш вопрос одним сообщением, и я отвечу по натальной карте.")


@router.message(AskState.waiting_for_question)
async def handle_question_state(message: Message, state) -> None:
    if not message.text:
        await message.answer("Пожалуйста, отправьте вопрос текстом.")
        return

    await _answer_question(message, message.text)
    await state.clear()


async def _answer_question(message: Message, question: str) -> None:
    if message.from_user is None:
        return

    chart = await _load_chart(message.from_user.id)
    if chart is None:
        await message.answer("Сначала создайте натальную карту через /start.")
        return

    async with AsyncSessionLocal() as session:
        user = await get_user(session, message.from_user.id)
        allowed, remaining = await can_ask_question(session, user)
        if not allowed:
            await message.answer(
                f"Лимит бесплатных вопросов исчерпан. Осталось: {remaining}. "
                "Откройте /settings для подписки."
            )
            return

    answer = await answer_personal_question(chart, question)
    await message.answer(answer)
    async with AsyncSessionLocal() as session:
        await create_reading(
            session,
            telegram_id=message.from_user.id,
            reading_type="ask",
            question=question,
            ai_response=answer,
        )


@router.message(Command("my_data"))
async def handle_my_data(message: Message) -> None:
    if message.from_user is None:
        return

    async with AsyncSessionLocal() as session:
        payload = await export_user_bundle(session, message.from_user.id)
        remaining = settings.free_daily_questions_limit - await count_daily_questions(
            session,
            message.from_user.id,
        )

    if not payload:
        await message.answer("Мы пока не сохранили ваши данные. Начните с /start.")
        return

    birth_data = payload.get("birth_data") or {}
    text = (
        f"Ваш профиль:\n"
        f"• Telegram ID: {payload['user']['telegram_id']}\n"
        f"• Тариф: {payload['user']['subscription_type']}\n"
        f"• GDPR consent: {'да' if payload['user']['gdpr_consent'] else 'нет'}\n"
        f"• Дата рождения: {birth_data.get('birth_date', '—')}\n"
        f"• Время рождения: {birth_data.get('birth_time', '—')}\n"
        f"• Место рождения: {birth_data.get('birth_place', '—')}\n"
        f"• Осталось бесплатных вопросов сегодня: {max(remaining, 0)}"
    )
    await message.answer(text)


@router.message(Command("export_data"))
async def handle_export_data(message: Message) -> None:
    if message.from_user is None:
        return

    async with AsyncSessionLocal() as session:
        payload = await export_user_bundle(session, message.from_user.id)

    if not payload:
        await message.answer("Нет данных для экспорта.")
        return

    document = BufferedInputFile(
        json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
        filename=f"stellarium-export-{message.from_user.id}.json",
    )
    await message.answer_document(document, caption="Ваш экспорт данных в JSON.")


@router.message(Command("delete_data"))
async def handle_delete_data(message: Message) -> None:
    await message.answer(
        "Удаление необратимо. Подтвердите, если хотите стереть аккаунт, карту и историю чтений.",
        reply_markup=delete_data_keyboard(),
    )


@router.callback_query(F.data == "delete:confirm")
async def handle_delete_confirm(callback) -> None:
    if callback.from_user is None:
        await callback.answer()
        return

    async with AsyncSessionLocal() as session:
        await delete_user_data(session, callback.from_user.id)
    await callback.message.answer("Все данные удалены. Вы можете заново пройти onboarding через /start.")
    await callback.answer("Данные удалены")


@router.callback_query(F.data == "delete:cancel")
async def handle_delete_cancel(callback) -> None:
    await callback.answer("Удаление отменено")


@router.callback_query(F.data.startswith("buy:"))
async def handle_buy_plan(callback) -> None:
    if callback.from_user is None:
        await callback.answer()
        return

    plan_code = callback.data.split(":")[1]
    if plan_code == "pro":
        title = "Stellarium Pro — месячная подписка"
        description = "Персональные прогнозы, совместимость и безлимитный ИИ-астролог."
        amount = PRO_PLAN.stars
    else:
        title = "Cosmic Oracle — месячная подписка"
        description = "Все из Pro плюс годовые прогнозы и бизнес-астрология."
        amount = ORACLE_PLAN.stars

    await callback.message.answer_invoice(
        title=title,
        description=description,
        payload=f"subscription:{plan_code}",
        currency="XTR",
        prices=[LabeledPrice(label=title, amount=amount)],
        start_parameter=f"buy-{plan_code}",
        is_flexible=False,
    )
    await callback.answer()


@router.pre_checkout_query()
async def handle_pre_checkout(pre_checkout_query: PreCheckoutQuery) -> None:
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def handle_successful_payment(message: Message) -> None:
    if message.from_user is None or message.successful_payment is None:
        return

    plan_code = "pro"
    if message.successful_payment.invoice_payload.endswith("oracle"):
        plan_code = "oracle"
        amount = ORACLE_PLAN.stars
    else:
        amount = PRO_PLAN.stars

    async with AsyncSessionLocal() as session:
        await add_subscription(
            session=session,
            telegram_id=message.from_user.id,
            plan_type=plan_code,
            stars_amount=amount,
            telegram_payment_charge_id=message.successful_payment.telegram_payment_charge_id,
            provider_payment_charge_id=message.successful_payment.provider_payment_charge_id,
        )

    await message.answer(
        "Оплата получена. Подписка активирована на 30 дней. "
        "Открывайте /week, /transit и /compatibility."
    )


@router.inline_query()
async def handle_inline_query(inline_query: InlineQuery) -> None:
    raw_query = inline_query.query.strip()
    if not raw_query:
        return

    parts = raw_query.split()
    result_text = "Попробуйте запросы: daily Virgo или compatibility Leo Scorpio"
    if len(parts) >= 2 and parts[0].lower() == "daily":
        result_text = sign_forecast(parts[1], "day")
    elif len(parts) >= 3 and parts[0].lower() == "compatibility":
        result_text = (
            f"{parts[1].capitalize()} + {parts[2].capitalize()}: союз с высоким уровнем "
            "магнетизма, который требует честного общения и уважения границ."
        )

    article = InlineQueryResultArticle(
        id="stellarium-inline-1",
        title="Stellarium AI preview",
        description="Preview for inline mode",
        input_message_content=InputTextMessageContent(
            message_text=f"{result_text}\n\n{DISCLAIMER_TEXT}",
            parse_mode=ParseMode.HTML,
        ),
    )
    await inline_query.answer([article], cache_time=1, is_personal=True)
