from aiogram.fsm.state import State, StatesGroup


class AddHabit(StatesGroup):
    name = State()
    emoji = State()
    description = State()
    frequency = State()
    custom_days = State()
    target = State()
    reminder = State()
    reminder_time = State()
    confirm = State()


class EditHabit(StatesGroup):
    waiting_value = State()
    custom_days = State()
    reminder_time = State()
