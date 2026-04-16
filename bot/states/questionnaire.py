from aiogram.fsm.state import State, StatesGroup

class QuestionnaireStates(StatesGroup):
    answering = State()
    multichoice_selecting = State()
