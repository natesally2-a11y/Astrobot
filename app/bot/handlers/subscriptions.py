"""Subscription settings, plan listing, /settings command."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, LabeledPrice, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import settings_kb, subscription_kb
from app.config import get_settings
from app.database.crud import has_active_subscription
from app.database.models import User
from app.payments import PLANS, get_plan

router = Router(name="subscriptions")


def _status_text(user: User) -> str:
    plan = user.subscription_type
    expires = user.subscription_expires_at
    if plan == "free" or not expires:
        return "Подписка: <b>Free</b>"
    return (
        f"Подписка: <b>{plan.upper()}</b>\n"
        f"Действует до: {expires.strftime('%d.%m.%Y')}"
    )


@router.message(Command("settings"))
async def cmd_settings(message: Message, user: User) -> None:
    is_premium = has_active_subscription(user)
    txt = ["⚙️ <b>Настройки</b>", "", _status_text(user)]
    await message.answer(
        "\n".join(txt),
        parse_mode="HTML",
        reply_markup=settings_kb(is_premium=is_premium),
    )


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message) -> None:
    await _show_plans(message)


async def _show_plans(message: Message) -> None:
    lines = [
        "💫 <b>Тарифные планы</b>",
        "",
        "<b>Free</b> — натальная карта, 5 вопросов в день",
        "",
    ]
    for plan in PLANS.values():
        lines.append(f"<b>{plan.title.split(' — ')[0]}</b> — {plan.price_rub}₽ / "
                     f"{plan.stars}⭐ в месяц")
        for perk in plan.perks:
            lines.append(f"  • {perk}")
        lines.append("")
    await message.answer(
        "\n".join(lines), parse_mode="HTML", reply_markup=subscription_kb()
    )


@router.callback_query(F.data == "settings:subscribe")
async def cb_settings_subscribe(cq: CallbackQuery) -> None:
    await _show_plans(cq.message)
    await cq.answer()


@router.callback_query(F.data == "settings:privacy")
async def cb_settings_privacy(cq: CallbackQuery) -> None:
    from app.bot import texts
    await cq.message.answer(texts.PRIVACY_SHORT)
    await cq.answer()


@router.callback_query(F.data == "settings:ref")
async def cb_settings_ref(cq: CallbackQuery, user: User) -> None:
    settings = get_settings()
    link = f"https://t.me/{settings.bot_username}?start=ref_{user.telegram_id}"
    await cq.message.answer(
        "🤝 <b>Реферальная программа</b>\n\n"
        f"Ваша персональная ссылка:\n<code>{link}</code>\n\n"
        f"За каждого друга, который зарегистрируется по ней, вы получаете "
        f"+7 дней Stellarium Pro.\n\n"
        f"Уже подарено бонусных дней: <b>{user.referral_bonus_days}</b>",
        parse_mode="HTML",
    )
    await cq.answer()


@router.callback_query(F.data == "settings:edit")
async def cb_settings_edit(cq: CallbackQuery) -> None:
    await cq.message.answer(
        "Чтобы заново ввести данные рождения, отправьте /start и пройдите "
        "опрос заново. Старые данные будут перезаписаны."
    )
    await cq.answer()


@router.callback_query(F.data.startswith("sub:buy:"))
async def cb_buy(cq: CallbackQuery, user: User) -> None:
    code = cq.data.split(":")[2]
    plan = get_plan(code)
    if plan is None:
        await cq.answer("План не найден", show_alert=True)
        return

    await cq.message.answer_invoice(
        title=plan.title,
        description=plan.description,
        payload=plan.payload,
        currency="XTR",
        prices=[LabeledPrice(label=plan.title, amount=plan.stars)],
        provider_token="",  # empty string for Stars (XTR)
        start_parameter=f"sub_{plan.code}",
    )
    await cq.answer()
