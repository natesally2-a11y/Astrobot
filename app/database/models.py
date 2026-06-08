"""SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

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


class SubscriptionTier:
    FREE = "free"
    PRO = "pro"
    ORACLE = "oracle"


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    username: Mapped[Optional[str]] = mapped_column(String(50))
    language_code: Mapped[Optional[str]] = mapped_column(String(8), default="ru")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    subscription_type: Mapped[str] = mapped_column(
        String(20), default=SubscriptionTier.FREE, nullable=False
    )
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    gdpr_consent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    gdpr_consent_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    referrer_id: Mapped[Optional[int]] = mapped_column(BigInteger)

    birth_data: Mapped[Optional["BirthData"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
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
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        primary_key=True,
    )
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    birth_time: Mapped[Optional[time]] = mapped_column(Time)
    birth_place: Mapped[str] = mapped_column(String(200), nullable=False)
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 8))
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(11, 8))
    timezone: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="birth_data")


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        index=True,
    )
    reading_type: Mapped[str] = mapped_column(String(50))
    question: Mapped[Optional[str]] = mapped_column(Text)
    ai_response: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    user: Mapped[User] = relationship(back_populates="readings")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        index=True,
    )
    plan_type: Mapped[str] = mapped_column(String(20))
    stars_amount: Mapped[int] = mapped_column(Integer)
    telegram_payment_charge_id: Mapped[Optional[str]] = mapped_column(String(255))
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship(back_populates="subscriptions")
