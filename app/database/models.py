from datetime import date, datetime, time

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    first_name: Mapped[str | None] = mapped_column(String(100))
    username: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    subscription_type: Mapped[str] = mapped_column(String(20), default="free")
    subscription_expires_at: Mapped[datetime | None] = mapped_column(DateTime)

    gdpr_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    gdpr_consent_date: Mapped[datetime | None] = mapped_column(DateTime)

    daily_questions_used: Mapped[int] = mapped_column(Integer, default=0)
    daily_questions_date: Mapped[date | None] = mapped_column(Date)

    birth_data: Mapped["BirthData"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    readings: Mapped[list["Reading"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class BirthData(Base):
    __tablename__ = "birth_data"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"), primary_key=True)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    birth_time: Mapped[time | None] = mapped_column(Time)
    birth_place: Mapped[str] = mapped_column(String(200), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    timezone: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="birth_data")


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"), nullable=False)
    reading_type: Mapped[str] = mapped_column(String(50), nullable=False)
    question: Mapped[str | None] = mapped_column(Text)
    ai_response: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="readings")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"), nullable=False)
    plan_type: Mapped[str] = mapped_column(String(20), nullable=False)
    stars_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship(back_populates="subscriptions")
