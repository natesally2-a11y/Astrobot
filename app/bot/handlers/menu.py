"""Inline-menu callback dispatcher."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.handlers import ask, chart, compatibility, forecasts, subscriptions
from app.bot.keyboards import main_menu_kb
from app.database.models import User

router = Router(name="menu")


@router.callback_query(F.data == "menu:back")
async def menu_back(cq: CallbackQuery) -> None:
    await cq.message.answer("Главное меню:", reply_markup=main_menu_kb())
    await cq.answer()


@router.callback_query(F.data == "menu:chart")
async def menu_chart(cq: CallbackQuery, session: AsyncSession, user: User) -> None:
    await chart.cmd_chart(cq.message, session=session, user=user)
    await cq.answer()


@router.callback_query(F.data == "menu:today")
async def menu_today(cq: CallbackQuery, session: AsyncSession, user: User) -> None:
    await forecasts.cmd_today(cq.message, session=session, user=user)
    await cq.answer()


@router.callback_query(F.data == "menu:transit")
async def menu_transit(cq: CallbackQuery, session: AsyncSession, user: User) -> None:
    await forecasts.cmd_transit(cq.message, session=session, user=user)
    await cq.answer()


@router.callback_query(F.data == "menu:ask")
async def menu_ask(
    cq: CallbackQuery, state: FSMContext, session: AsyncSession, user: User
) -> None:
    await ask.cmd_ask(cq.message, session=session, user=user, state=state)
    await cq.answer()


@router.callback_query(F.data == "menu:compat")
async def menu_compat(
    cq: CallbackQuery, state: FSMContext, session: AsyncSession, user: User
) -> None:
    await compatibility.cmd_compatibility(
        cq.message, session=session, user=user, state=state
    )
    await cq.answer()


@router.callback_query(F.data == "menu:settings")
async def menu_settings(cq: CallbackQuery, user: User) -> None:
    await subscriptions.cmd_settings(cq.message, user=user)
    await cq.answer()
