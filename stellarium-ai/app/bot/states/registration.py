from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    waiting_for_gdpr = State()
    waiting_for_birth_year = State()
    waiting_for_birth_month = State()
    waiting_for_birth_day = State()
    waiting_for_birth_time = State()
    waiting_for_birth_place = State()
    confirming_data = State()


class CompatibilityStates(StatesGroup):
    waiting_for_partner_name = State()
    waiting_for_partner_year = State()
    waiting_for_partner_month = State()
    waiting_for_partner_day = State()
    waiting_for_partner_time = State()
    waiting_for_partner_place = State()


class AskStates(StatesGroup):
    waiting_for_question = State()
