"""ORM models for Stellarium AI."""
from __future__ import annotations

from datetime import date, datetime, time
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

from app.database.session import Base


class User(Base):
    """Telegram user with subscription info and GDPR consent state."""

    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    username: Mapped[Optional[str]] = mapped_column(String(50))
    language_code: Mapped[Optional[str]] = mapped_column(String(10))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    subscription_type: Mapped[str] = mapped_column(String(20), default="free")
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    gdpr_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    gdpr_consent_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    # Referral system
    referred_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    referral_bonus_days: Mapped[int] = mapped_column(Integer, default=0)

    # Daily quota tracker (for Free users)
    free_questions_used: Mapped[int] = mapped_column(Integer, default=0)
    free_questions_reset_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

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
    """User's natal data — required to compute a chart."""

    __tablename__ = "birth_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), unique=True
    )
    name: Mapped[Optional[str]] = mapped_column(String(100))
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    birth_time: Mapped[Optional[time]] = mapped_column(Time)
    time_is_unknown: Mapped[bool] = mapped_column(Boolean, default=False)
    birth_place: Mapped[str] = mapped_column(String(200), nullable=False)
    latitude: Mapped[float] = mapped_column(Numeric(10, 6))
    longitude: Mapped[float] = mapped_column(Numeric(11, 6))
    timezone: Mapped[Optional[str]] = mapped_column(String(50))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="birth_data")


class Reading(Base):
    """Persisted history of AI readings."""

    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE")
    )
    reading_type: Mapped[str] = mapped_column(String(50))
    question: Mapped[Optional[str]] = mapped_column(Text)
    ai_response: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="readings")


class Subscription(Base):
    """A purchased subscription tracked from Telegram Stars payments."""

    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE")
    )
    plan_type: Mapped[str] = mapped_column(String(20))
    stars_amount: Mapped[int] = mapped_column(Integer)
    telegram_payment_charge_id: Mapped[Optional[str]] = mapped_column(String(200))
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="subscriptions")
