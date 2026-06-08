"""FSM state groups."""
from aiogram.fsm.state import State, StatesGroup


class Onboarding(StatesGroup):
    waiting_consent = State()
    waiting_name = State()
    waiting_date = State()
    waiting_time = State()
    waiting_place = State()
    waiting_place_choice = State()


class AskFlow(StatesGroup):
    waiting_question = State()


class CompatibilityFlow(StatesGroup):
    waiting_partner = State()
