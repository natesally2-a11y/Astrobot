from aiogram import F, Router
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from app.config import get_settings
from app.database.crud import activate_subscription
from app.database.models import SubscriptionType
from app.database.session import async_session

router = Router(name="payments")

PLAN_PAYLOADS = {
    "pay:pro": {
        "plan": SubscriptionType.PRO.value,
        "title": "Stellarium Pro — месячная подписка",
        "description": "Подробные прогнозы, совместимость, транзиты и безлимитные вопросы ИИ.",
        "payload": "stellarium_pro_monthly",
        "label": "Stellarium Pro",
        "stars_setting": "pro_stars_amount",
    },
    "pay:oracle": {
        "plan": SubscriptionType.ORACLE.value,
        "title": "Космический Оракул — месячная подписка",
        "description": "Все возможности Pro плюс бизнес-астрология, годовые прогнозы и приоритетный ИИ.",
        "payload": "stellarium_oracle_monthly",
        "label": "Космический Оракул",
        "stars_setting": "oracle_stars_amount",
    },
}

PAYLOAD_TO_PLAN = {plan["payload"]: plan for plan in PLAN_PAYLOADS.values()}


@router.callback_query(F.data.in_(PLAN_PAYLOADS.keys()))
async def create_invoice(callback: CallbackQuery) -> None:
    plan = PLAN_PAYLOADS[callback.data or ""]
    settings = get_settings()
    amount = getattr(settings, str(plan["stars_setting"]))

    await callback.bot.send_invoice(
        chat_id=callback.from_user.id,
        title=str(plan["title"]),
        description=str(plan["description"]),
        payload=str(plan["payload"]),
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=str(plan["label"]), amount=amount)],
    )
    await callback.answer()


@router.pre_checkout_query()
async def approve_pre_checkout(pre_checkout_query: PreCheckoutQuery) -> None:
    if pre_checkout_query.invoice_payload not in PAYLOAD_TO_PLAN:
        await pre_checkout_query.answer(ok=False, error_message="Неизвестный тариф.")
        return
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message) -> None:
    if message.from_user is None or message.successful_payment is None:
        return

    payload = message.successful_payment.invoice_payload
    plan = PAYLOAD_TO_PLAN.get(payload)
    if plan is None:
        await message.answer("Платеж получен, но тариф не распознан. Напишите в поддержку.")
        return

    async with async_session() as session:
        subscription = await activate_subscription(
            session=session,
            user_id=message.from_user.id,
            plan_type=str(plan["plan"]),
            stars_amount=message.successful_payment.total_amount,
            telegram_payment_charge_id=message.successful_payment.telegram_payment_charge_id,
        )

    await message.answer(
        "✨ Подписка активирована!\n"
        f"Тариф: {plan['label']}\n"
        f"Действует до: {subscription.expires_at.strftime('%d.%m.%Y') if subscription.expires_at else 'не задано'}\n\n"
        "Возвраты и спорные платежи обрабатываются через правила Telegram Stars."
    )
