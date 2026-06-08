"""ORM-модели Stellarium AI."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    first_name: Mapped[str | None] = mapped_column(String(100))
    username: Mapped[str | None] = mapped_column(String(50))
    language_code: Mapped[str] = mapped_column(String(8), default="ru")
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    subscription_type: Mapped[str] = mapped_column(String(20), default="free")
    subscription_expires_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    gdpr_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    gdpr_consent_date: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    # Учёт лимита бесплатных вопросов
    ask_count: Mapped[int] = mapped_column(Integer, default=0)
    ask_count_date: Mapped[dt.date | None] = mapped_column(Date)

    # Реферальная система
    referred_by: Mapped[int | None] = mapped_column(BigInteger)
    referral_count: Mapped[int] = mapped_column(Integer, default=0)

    birth_data: Mapped["BirthData | None"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    readings: Mapped[list["Reading"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class BirthData(Base):
    __tablename__ = "birth_data"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), primary_key=True
    )
    birth_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    birth_time: Mapped[dt.time | None] = mapped_column(Time)
    time_is_exact: Mapped[bool] = mapped_column(Boolean, default=True)
    birth_place: Mapped[str] = mapped_column(String(200), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 6))
    longitude: Mapped[float | None] = mapped_column(Numeric(11, 6))
    timezone: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="birth_data")


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE")
    )
    reading_type: Mapped[str] = mapped_column(String(50))  # natal, daily, weekly...
    question: Mapped[str | None] = mapped_column(Text)
    ai_response: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="readings")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE")
    )
    plan_type: Mapped[str] = mapped_column(String(20))
    stars_amount: Mapped[int] = mapped_column(Integer, default=0)
    telegram_charge_id: Mapped[str | None] = mapped_column(String(128))
    started_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="subscriptions")
