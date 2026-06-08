"""SQLAlchemy ORM models for Stellarium AI."""
from __future__ import annotations

import datetime as dt
from typing import List, Optional

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

from app.database.base import Base

# Subscription tiers
PLAN_FREE = "free"
PLAN_PRO = "pro"
PLAN_ORACLE = "oracle"


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    username: Mapped[Optional[str]] = mapped_column(String(64))
    language_code: Mapped[Optional[str]] = mapped_column(String(10), default="ru")

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    subscription_type: Mapped[str] = mapped_column(String(20), default=PLAN_FREE)
    subscription_expires_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True))

    # GDPR / 152-ФЗ
    gdpr_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    gdpr_consent_date: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True))

    # Free-tier daily quota tracking
    questions_used_today: Mapped[int] = mapped_column(Integer, default=0)
    questions_quota_date: Mapped[Optional[dt.date]] = mapped_column(Date)

    # Referral system
    referred_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    referral_count: Mapped[int] = mapped_column(Integer, default=0)

    birth_data: Mapped[Optional["BirthData"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    readings: Mapped[List["Reading"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[List["Subscription"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class BirthData(Base):
    __tablename__ = "birth_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), unique=True
    )

    birth_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    birth_time: Mapped[Optional[dt.time]] = mapped_column(Time)
    time_known: Mapped[bool] = mapped_column(Boolean, default=True)

    birth_place: Mapped[str] = mapped_column(String(200), nullable=False)
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(11, 6))
    timezone: Mapped[Optional[str]] = mapped_column(String(64))

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="birth_data")


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE")
    )
    reading_type: Mapped[str] = mapped_column(String(50))  # natal/daily/weekly/compatibility/transit/ask
    question: Mapped[Optional[str]] = mapped_column(Text)
    ai_response: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="readings")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE")
    )
    plan_type: Mapped[str] = mapped_column(String(20))
    stars_amount: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True))
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False)
    telegram_payment_charge_id: Mapped[Optional[str]] = mapped_column(String(255))

    user: Mapped["User"] = relationship(back_populates="subscriptions")
