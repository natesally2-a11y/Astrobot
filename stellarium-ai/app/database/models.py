from datetime import datetime, date, time
from typing import Optional
from sqlalchemy import (
    BigInteger, String, Boolean, DateTime, Date, Time,
    Numeric, Integer, Text, ForeignKey, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.connection import Base


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    username: Mapped[Optional[str]] = mapped_column(String(50))
    language_code: Mapped[Optional[str]] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    subscription_type: Mapped[str] = mapped_column(String(20), default="free")
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    gdpr_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    gdpr_consent_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    referred_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    questions_today: Mapped[int] = mapped_column(Integer, default=0)
    questions_reset_date: Mapped[Optional[date]] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    birth_data: Mapped[Optional["BirthData"]] = relationship(
        back_populates="user", uselist=False
    )
    readings: Mapped[list["Reading"]] = relationship(back_populates="user")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user")

    @property
    def display_name(self) -> str:
        if self.first_name:
            return self.first_name
        if self.username:
            return f"@{self.username}"
        return f"User {self.telegram_id}"

    @property
    def is_pro(self) -> bool:
        if self.subscription_type in ("pro", "oracle"):
            if self.subscription_expires_at and self.subscription_expires_at > datetime.utcnow():
                return True
        return False

    @property
    def is_oracle(self) -> bool:
        if self.subscription_type == "oracle":
            if self.subscription_expires_at and self.subscription_expires_at > datetime.utcnow():
                return True
        return False


class BirthData(Base):
    __tablename__ = "birth_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"))
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    birth_time: Mapped[Optional[time]] = mapped_column(Time)
    birth_place: Mapped[str] = mapped_column(String(200), nullable=False)
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 8))
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(11, 8))
    timezone: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="birth_data")


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"))
    reading_type: Mapped[str] = mapped_column(String(50))
    question: Mapped[Optional[str]] = mapped_column(Text)
    ai_response: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="readings")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"))
    plan_type: Mapped[str] = mapped_column(String(20))
    stars_amount: Mapped[int] = mapped_column(Integer)
    payment_id: Mapped[Optional[str]] = mapped_column(String(100))
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship(back_populates="subscriptions")
