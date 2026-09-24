from keyboards.calendar import calendar_kb, day_habits_kb
from keyboards.habits import (
    add_confirm_kb,
    add_description_kb,
    add_frequency_kb,
    add_reminder_kb,
    custom_days_kb,
    habit_actions_kb,
    habit_quantity_kb,
    habits_list_kb,
)
from keyboards.main import about_kb, main_menu_kb
from keyboards.settings import (
    delete_confirm_kb,
    settings_kb,
    time_format_kb,
    timezone_kb,
)

__all__ = [
    "about_kb",
    "add_confirm_kb",
    "add_description_kb",
    "add_frequency_kb",
    "add_reminder_kb",
    "calendar_kb",
    "custom_days_kb",
    "day_habits_kb",
    "delete_confirm_kb",
    "habit_actions_kb",
    "habit_quantity_kb",
    "habits_list_kb",
    "main_menu_kb",
    "settings_kb",
    "time_format_kb",
    "timezone_kb",
]
