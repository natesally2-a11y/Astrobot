from aiogram.fsm.state import State, StatesGroup


class OnboardingState(StatesGroup):
    waiting_for_consent = State()
    waiting_for_year = State()
    waiting_for_month = State()
    waiting_for_day = State()
    waiting_for_hour = State()
    waiting_for_minute = State()
    waiting_for_place_query = State()
    waiting_for_place_choice = State()


class AskState(StatesGroup):
    waiting_for_question = State()


class CompatibilityState(StatesGroup):
    waiting_for_partner_data = State()


class DeleteDataState(StatesGroup):
    waiting_for_confirmation = State()
