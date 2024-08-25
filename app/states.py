from aiogram.fsm.state import State, StatesGroup





class TestStates(StatesGroup):
    answering_question = State()


class AdminStates(StatesGroup):
    waiting_for_broadcast_message = State()