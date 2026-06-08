from datetime import date, datetime, timedelta, timezone

from app.database.crud import create_reading, get_recent_readings, get_user, save_birth_data, upsert_user
from app.database.session import async_session_factory

DEMO_TELEGRAM_ID = 777000


async def seed_demo_data() -> None:
    async with async_session_factory() as session:
        user = await get_user(session, DEMO_TELEGRAM_ID)
        if user is None:
            user = await upsert_user(session, DEMO_TELEGRAM_ID, 'Demo', 'stellarium_demo')
            user.subscription_type = 'oracle'
            user.subscription_expires_at = datetime.now(timezone.utc) + timedelta(days=90)
            user.gdpr_consent = True
            user.gdpr_consent_date = datetime.now(timezone.utc)
            await session.commit()
            user = await get_user(session, DEMO_TELEGRAM_ID)
        if user.birth_data is None:
            await save_birth_data(
                session,
                DEMO_TELEGRAM_ID,
                birth_date=date(1991, 8, 15),
                birth_time=datetime.strptime('09:35', '%H:%M').time(),
                birth_place='Moscow, Russia',
                latitude=55.7558,
                longitude=37.6176,
                timezone_name='Europe/Moscow',
                is_time_approximate=False,
            )
        readings = await get_recent_readings(session, DEMO_TELEGRAM_ID, limit=1)
        if not readings:
            await create_reading(
                session,
                DEMO_TELEGRAM_ID,
                'daily',
                'Демо-прогноз: сегодня полезно совмещать практичность с интуицией и не перегружать себя лишними обещаниями.',
            )


if __name__ == '__main__':
    import asyncio

    asyncio.run(seed_demo_data())
