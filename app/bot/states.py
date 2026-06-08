"""FSM states for multi-step dialogs."""
from aiogram.fsm.state import State, StatesGroup


class Onboarding(StatesGroup):
    date = State()
    time = State()
    place = State()
    place_choice = State()
    consent = State()


class AskFlow(StatesGroup):
    waiting_question = State()


class CompatibilityFlow(StatesGroup):
    partner_date = State()
    partner_time = State()
    partner_place = State()
