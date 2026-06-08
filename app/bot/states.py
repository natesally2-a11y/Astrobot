from aiogram.fsm.state import State, StatesGroup


class Onboarding(StatesGroup):
    waiting_birth_date = State()
    waiting_birth_time = State()
    waiting_birth_place = State()
    waiting_consent = State()


class AskAstrologer(StatesGroup):
    waiting_question = State()


class Compatibility(StatesGroup):
    waiting_partner_date = State()
    waiting_partner_time = State()
    waiting_partner_place = State()
