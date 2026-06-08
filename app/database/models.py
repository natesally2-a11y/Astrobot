from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    telegram_id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str | None] = mapped_column(String(100))
    username: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    subscription_type: Mapped[str] = mapped_column(String(20), default='free', server_default='free')
    subscription_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    gdpr_consent: Mapped[bool] = mapped_column(Boolean, default=False, server_default='false')
    gdpr_consent_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    birth_data: Mapped['BirthData | None'] = relationship(back_populates='user', cascade='all, delete-orphan', uselist=False)
    readings: Mapped[list['Reading']] = relationship(back_populates='user', cascade='all, delete-orphan')
    subscriptions: Mapped[list['Subscription']] = relationship(back_populates='user', cascade='all, delete-orphan')


class BirthData(Base):
    __tablename__ = 'birth_data'

    user_id: Mapped[int] = mapped_column(ForeignKey('users.telegram_id', ondelete='CASCADE'), primary_key=True)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    birth_time: Mapped[time | None] = mapped_column(nullable=True)
    birth_place: Mapped[str] = mapped_column(String(200), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 8))
    longitude: Mapped[float | None] = mapped_column(Numeric(11, 8))
    timezone: Mapped[str | None] = mapped_column(String(50))
    is_time_approximate: Mapped[bool] = mapped_column(Boolean, default=False, server_default='false')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates='birth_data')


class Reading(Base):
    __tablename__ = 'readings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.telegram_id', ondelete='CASCADE'))
    reading_type: Mapped[str] = mapped_column(String(50), nullable=False)
    question: Mapped[str | None] = mapped_column(Text)
    ai_response: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates='readings')


class Subscription(Base):
    __tablename__ = 'subscriptions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.telegram_id', ondelete='CASCADE'))
    plan_type: Mapped[str] = mapped_column(String(20), nullable=False)
    stars_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True, server_default='true')
    status: Mapped[str] = mapped_column(String(20), default='active', server_default='active')

    user: Mapped[User] = relationship(back_populates='subscriptions')
