from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.database.models import Base

logger = logging.getLogger(__name__)
settings = get_settings()
engine = create_async_engine(settings.sqlalchemy_database_url, echo=settings.environment == "development")
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db(retries: int = 10, delay_seconds: float = 2.0) -> None:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialized")
            return
        except Exception as exc:  # pragma: no cover - depends on deployment timing
            last_error = exc
            if attempt == retries:
                break
            logger.warning("Database is not ready yet (%s/%s): %s", attempt, retries, exc)
            await asyncio.sleep(delay_seconds)
    raise RuntimeError("Database initialization failed") from last_error


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
