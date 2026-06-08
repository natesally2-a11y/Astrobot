from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    username: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    subscription_type: Mapped[str] = mapped_column(String(20), default="free")
    subscription_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    gdpr_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    gdpr_consent_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    referred_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.telegram_id"),
        nullable=True,
    )

    birth_data: Mapped["BirthData | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    readings: Mapped[list["Reading"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class BirthData(Base):
    __tablename__ = "birth_data"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        primary_key=True,
    )
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    birth_time: Mapped[time | None] = mapped_column(nullable=True)
    birth_place: Mapped[str] = mapped_column(String(200), nullable=False)
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False)
    is_time_approximate: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    raw_geocoding_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    user: Mapped["User"] = relationship(back_populates="birth_data")


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
    )
    reading_type: Mapped[str] = mapped_column(String(50), nullable=False)
    question: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_response: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="readings")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
    )
    plan_type: Mapped[str] = mapped_column(String(20), nullable=False)
    stars_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True)
    telegram_payment_charge_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_payment_charge_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship(back_populates="subscriptions")
