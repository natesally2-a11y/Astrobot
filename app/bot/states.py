from aiogram.fsm.state import State, StatesGroup


class Onboarding(StatesGroup):
    waiting_for_birth_date = State()
    waiting_for_birth_time = State()
    waiting_for_birth_place = State()
    waiting_for_city_choice = State()
    waiting_for_consent = State()


class AskAstrologer(StatesGroup):
    waiting_for_question = State()


class Compatibility(StatesGroup):
    waiting_for_partner_data = State()
