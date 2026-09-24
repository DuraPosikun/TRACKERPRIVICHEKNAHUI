from aiogram.fsm.state import State, StatesGroup


class DeleteAccount(StatesGroup):
    confirm = State()


class EditSettings(StatesGroup):
    timezone = State()
