from aiogram import F, Router
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from app.config import settings
from app.database.crud import create_subscription
from app.database.session import async_session_factory

router = Router(name='payments')

PLAN_CONFIG = {
    'pro': {
        'title': 'Stellarium Pro — месячная подписка',
        'description': 'Подробные прогнозы, weekly, compatibility и безлимитные AI-вопросы.',
        'payload': 'stellarium_pro_monthly',
        'stars': settings.pro_plan_stars,
    },
    'oracle': {
        'title': 'Cosmic Oracle — месячная подписка',
        'description': 'Все возможности Pro + бизнес-астрология, годовые прогнозы и индивидуальные рекомендации.',
        'payload': 'stellarium_oracle_monthly',
        'stars': settings.oracle_plan_stars,
    },
}


@router.callback_query(F.data.startswith('buy:'))
async def buy_plan(callback: CallbackQuery, bot) -> None:
    plan = callback.data.split(':')[1]
    config = PLAN_CONFIG[plan]
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=config['title'],
        description=config['description'],
        payload=config['payload'],
        currency='XTR',
        prices=[LabeledPrice(label=config['title'], amount=config['stars'])],
    )
    await callback.answer('Инвойс отправлен')


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery, bot) -> None:
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message) -> None:
    payload = message.successful_payment.invoice_payload
    if 'oracle' in payload:
        plan_type = 'oracle'
        stars_amount = settings.oracle_plan_stars
    else:
        plan_type = 'pro'
        stars_amount = settings.pro_plan_stars
    async with async_session_factory() as session:
        await create_subscription(session, message.from_user.id, plan_type, stars_amount)
    await message.answer('✨ Платеж получен. Подписка активирована и premium-функции уже доступны.')
