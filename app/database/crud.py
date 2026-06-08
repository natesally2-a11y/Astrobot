"""CRUD-операции над сущностями Stellarium AI."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import BirthData, Reading, Subscription, User
from app.plans import FREE, get_plan


async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(
        select(User)
        .where(User.telegram_id == telegram_id)
        .options(selectinload(User.birth_data))
    )
    return result.scalar_one_or_none()


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    first_name: str | None = None,
    username: str | None = None,
    language_code: str = "ru",
    referred_by: int | None = None,
) -> tuple[User, bool]:
    """Возвращает (user, created)."""
    user = await get_user(session, telegram_id)
    if user:
        # Обновим базовые поля профиля
        if first_name:
            user.first_name = first_name
        user.username = username
        await session.commit()
        return user, False

    user = User(
        telegram_id=telegram_id,
        first_name=first_name,
        username=username,
        language_code=language_code or "ru",
        subscription_type=FREE,
        referred_by=referred_by if referred_by != telegram_id else None,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user, True


async def set_gdpr_consent(session: AsyncSession, telegram_id: int) -> None:
    user = await get_user(session, telegram_id)
    if user:
        user.gdpr_consent = True
        user.gdpr_consent_date = dt.datetime.now(dt.timezone.utc)
        await session.commit()


async def upsert_birth_data(
    session: AsyncSession,
    telegram_id: int,
    birth_date: dt.date,
    birth_time: dt.time | None,
    time_is_exact: bool,
    birth_place: str,
    latitude: float | None,
    longitude: float | None,
    timezone: str | None,
) -> BirthData:
    result = await session.execute(
        select(BirthData).where(BirthData.user_id == telegram_id)
    )
    bd = result.scalar_one_or_none()
    if bd is None:
        bd = BirthData(user_id=telegram_id)
        session.add(bd)

    bd.birth_date = birth_date
    bd.birth_time = birth_time
    bd.time_is_exact = time_is_exact
    bd.birth_place = birth_place
    bd.latitude = latitude
    bd.longitude = longitude
    bd.timezone = timezone
    await session.commit()
    await session.refresh(bd)
    return bd


async def get_birth_data(
    session: AsyncSession, telegram_id: int
) -> BirthData | None:
    result = await session.execute(
        select(BirthData).where(BirthData.user_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def save_reading(
    session: AsyncSession,
    telegram_id: int,
    reading_type: str,
    ai_response: str,
    question: str | None = None,
) -> Reading:
    reading = Reading(
        user_id=telegram_id,
        reading_type=reading_type,
        question=question,
        ai_response=ai_response,
    )
    session.add(reading)
    await session.commit()
    await session.refresh(reading)
    return reading


async def get_readings(
    session: AsyncSession, telegram_id: int, limit: int = 20
) -> list[Reading]:
    result = await session.execute(
        select(Reading)
        .where(Reading.user_id == telegram_id)
        .order_by(Reading.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


# ----------------------- Лимиты бесплатных вопросов -----------------------

async def check_and_increment_ask(session: AsyncSession, telegram_id: int) -> bool:
    """Проверяет дневной лимит вопросов и инкрементирует счётчик.

    Возвращает True, если вопрос разрешён.
    """
    user = await get_user(session, telegram_id)
    if user is None:
        return False

    plan = get_plan(user.subscription_type)
    # Премиум: безлимит
    if plan.daily_ask_limit < 0 and is_subscription_active(user):
        return True

    today = dt.date.today()
    if user.ask_count_date != today:
        user.ask_count = 0
        user.ask_count_date = today

    limit = get_plan(FREE).daily_ask_limit
    if user.ask_count >= limit:
        await session.commit()
        return False

    user.ask_count += 1
    await session.commit()
    return True


def is_subscription_active(user: User) -> bool:
    if user.subscription_type == FREE:
        return False
    if user.subscription_expires_at is None:
        return False
    now = dt.datetime.now(dt.timezone.utc)
    expires = user.subscription_expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=dt.timezone.utc)
    return expires > now


# ----------------------- Подписки -----------------------

async def activate_subscription(
    session: AsyncSession,
    telegram_id: int,
    plan_code: str,
    stars_amount: int,
    duration_days: int,
    telegram_charge_id: str | None = None,
) -> Subscription:
    user = await get_user(session, telegram_id)
    now = dt.datetime.now(dt.timezone.utc)

    # Продление: если активна, добавляем к текущей дате окончания
    base = now
    if user and is_subscription_active(user) and user.subscription_expires_at:
        base = user.subscription_expires_at
        if base.tzinfo is None:
            base = base.replace(tzinfo=dt.timezone.utc)
    expires_at = base + dt.timedelta(days=duration_days)

    if user:
        user.subscription_type = plan_code
        user.subscription_expires_at = expires_at

    sub = Subscription(
        user_id=telegram_id,
        plan_type=plan_code,
        stars_amount=stars_amount,
        telegram_charge_id=telegram_charge_id,
        expires_at=expires_at,
        auto_renew=False,
    )
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    return sub


async def grant_referral_bonus(session: AsyncSession, referrer_id: int) -> None:
    """+1 неделя Pro рефереру за приглашённого друга."""
    user = await get_user(session, referrer_id)
    if not user:
        return
    user.referral_count += 1
    now = dt.datetime.now(dt.timezone.utc)
    base = now
    if is_subscription_active(user) and user.subscription_expires_at:
        base = user.subscription_expires_at
        if base.tzinfo is None:
            base = base.replace(tzinfo=dt.timezone.utc)
    if user.subscription_type == FREE:
        user.subscription_type = "pro"
    user.subscription_expires_at = base + dt.timedelta(days=7)
    await session.commit()


# ----------------------- GDPR -----------------------

async def export_user_data(session: AsyncSession, telegram_id: int) -> dict:
    user = await get_user(session, telegram_id)
    if not user:
        return {}
    bd = await get_birth_data(session, telegram_id)
    readings = await get_readings(session, telegram_id, limit=1000)

    def iso(value):
        return value.isoformat() if value else None

    return {
        "user": {
            "telegram_id": user.telegram_id,
            "first_name": user.first_name,
            "username": user.username,
            "language_code": user.language_code,
            "created_at": iso(user.created_at),
            "subscription_type": user.subscription_type,
            "subscription_expires_at": iso(user.subscription_expires_at),
            "gdpr_consent": user.gdpr_consent,
            "gdpr_consent_date": iso(user.gdpr_consent_date),
            "referral_count": user.referral_count,
        },
        "birth_data": None
        if not bd
        else {
            "birth_date": iso(bd.birth_date),
            "birth_time": bd.birth_time.isoformat() if bd.birth_time else None,
            "time_is_exact": bd.time_is_exact,
            "birth_place": bd.birth_place,
            "latitude": float(bd.latitude) if bd.latitude is not None else None,
            "longitude": float(bd.longitude) if bd.longitude is not None else None,
            "timezone": bd.timezone,
        },
        "readings": [
            {
                "type": r.reading_type,
                "question": r.question,
                "response": r.ai_response,
                "created_at": iso(r.created_at),
            }
            for r in readings
        ],
    }


async def delete_user_data(session: AsyncSession, telegram_id: int) -> None:
    """Право на забвение: полностью удалить пользователя и связанные данные."""
    await session.execute(delete(User).where(User.telegram_id == telegram_id))
    await session.commit()
