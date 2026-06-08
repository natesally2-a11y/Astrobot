from aiogram.fsm.state import State, StatesGroup


class OnboardingState(StatesGroup):
    waiting_birth_date = State()
    waiting_birth_time = State()
    waiting_birth_place = State()
    waiting_gdpr_consent = State()
