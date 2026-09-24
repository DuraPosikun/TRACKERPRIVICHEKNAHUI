from aiogram.fsm.state import State, StatesGroup


class AddLolzCustom(StatesGroup):
    title = State()
    emoji = State()
    frequency = State()


class AdminLolzTemplate(StatesGroup):
    title = State()
    emoji = State()
    category = State()
    frequency = State()
    description = State()
    rename = State()
