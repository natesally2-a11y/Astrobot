from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    waiting_birth_date = State()
    waiting_birth_time = State()
    waiting_birth_place = State()
    waiting_place_confirm = State()
    waiting_gdpr_consent = State()


class CompatibilityStates(StatesGroup):
    waiting_partner_name = State()
    waiting_partner_date = State()
    waiting_partner_time = State()
    waiting_partner_place = State()


class AskStates(StatesGroup):
    waiting_question = State()
