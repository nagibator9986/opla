from aiogram.fsm.state import State, StatesGroup

class OnboardingStates(StatesGroup):
    waiting_name = State()
    waiting_company = State()
    waiting_industry = State()
    waiting_phone = State()
    waiting_city = State()
