"""FSM-состояния диалогов бота."""
from aiogram.fsm.state import State, StatesGroup


class Onboarding(StatesGroup):
    date = State()
    time = State()
    place = State()


class AskFlow(StatesGroup):
    question = State()


class CompatibilityFlow(StatesGroup):
    name = State()
    date = State()
    time = State()
    place = State()
