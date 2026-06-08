from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    waiting_for_consent = State()
    waiting_for_birth_date = State()
    waiting_for_birth_time = State()
    waiting_for_birth_place = State()
    waiting_for_place_choice = State()


class InteractionStates(StatesGroup):
    waiting_for_question = State()
    waiting_for_partner_data = State()
    waiting_for_delete_confirmation = State()
