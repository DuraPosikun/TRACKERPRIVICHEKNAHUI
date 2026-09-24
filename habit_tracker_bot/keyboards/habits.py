from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import Habit
from utils.dates import WEEKDAY_SHORT


def habits_list_kb(habits: list[Habit], marks: dict[int, bool]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if not habits:
        builder.row(InlineKeyboardButton(text="➕ Добавить первую", callback_data="menu:add"))
    for habit in habits:
        check = "☑️" if marks.get(habit.id) else "⬜"
        builder.row(
            InlineKeyboardButton(
                text=f"{check} {habit.emoji} {habit.name}",
                callback_data=f"h:v:{habit.id}",
            )
        )
    builder.row(
        InlineKeyboardButton(text="➕ Добавить", callback_data="menu:add"),
        InlineKeyboardButton(text="↩️ Меню", callback_data="menu:main"),
    )
    return builder.as_markup()


def habit_actions_kb(habit: Habit, *, done: bool, value: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if habit.target > 1:
        builder.row(
            InlineKeyboardButton(text="−", callback_data=f"h:dec:{habit.id}"),
            InlineKeyboardButton(text=f"{value}/{habit.target}", callback_data=f"h:v:{habit.id}"),
            InlineKeyboardButton(text="+", callback_data=f"h:inc:{habit.id}"),
        )
    else:
        if done:
            builder.row(InlineKeyboardButton(text="☑️ Выполнено — снять", callback_data=f"h:tg:{habit.id}"))
        else:
            builder.row(InlineKeyboardButton(text="⬜ Отметить выполнение", callback_data=f"h:tg:{habit.id}"))
    builder.row(
        InlineKeyboardButton(text="✏️ Изменить", callback_data=f"h:ed:{habit.id}"),
        InlineKeyboardButton(text="🗑 Удалить", callback_data=f"h:dl:{habit.id}"),
    )
    builder.row(InlineKeyboardButton(text="↩️ К списку", callback_data="menu:habits"))
    return builder.as_markup()


def habit_quantity_kb(habit_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="−", callback_data=f"h:dec:{habit_id}"),
        InlineKeyboardButton(text="+", callback_data=f"h:inc:{habit_id}"),
    )
    builder.row(InlineKeyboardButton(text="↩️ Назад", callback_data=f"h:v:{habit_id}"))
    return builder.as_markup()


def habit_edit_fields_kb(habit_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Название", callback_data=f"h:ef:{habit_id}:name"))
    builder.row(InlineKeyboardButton(text="Эмодзи", callback_data=f"h:ef:{habit_id}:emoji"))
    builder.row(InlineKeyboardButton(text="Описание", callback_data=f"h:ef:{habit_id}:desc"))
    builder.row(InlineKeyboardButton(text="Периодичность", callback_data=f"h:ef:{habit_id}:freq"))
    builder.row(InlineKeyboardButton(text="Цель", callback_data=f"h:ef:{habit_id}:target"))
    builder.row(InlineKeyboardButton(text="Напоминание", callback_data=f"h:ef:{habit_id}:rem"))
    builder.row(InlineKeyboardButton(text="Время напоминания", callback_data=f"h:ef:{habit_id}:rtime"))
    builder.row(InlineKeyboardButton(text="↩️ Назад", callback_data=f"h:v:{habit_id}"))
    return builder.as_markup()


def delete_habit_kb(habit_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌ Да, удалить", callback_data=f"h:dx:{habit_id}"),
        InlineKeyboardButton(text="↩️ Отмена", callback_data=f"h:v:{habit_id}"),
    )
    return builder.as_markup()


def add_cancel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="add:cancel"))
    return builder.as_markup()


def add_description_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Пропустить", callback_data="add:skip_desc"))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="add:cancel"))
    return builder.as_markup()


def add_frequency_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Каждый день", callback_data="add:freq:daily"))
    builder.row(
        InlineKeyboardButton(text="Пн", callback_data="add:freq:0"),
        InlineKeyboardButton(text="Вт", callback_data="add:freq:1"),
        InlineKeyboardButton(text="Ср", callback_data="add:freq:2"),
        InlineKeyboardButton(text="Чт", callback_data="add:freq:3"),
    )
    builder.row(
        InlineKeyboardButton(text="Пт", callback_data="add:freq:4"),
        InlineKeyboardButton(text="Сб", callback_data="add:freq:5"),
        InlineKeyboardButton(text="Вс", callback_data="add:freq:6"),
    )
    builder.row(InlineKeyboardButton(text="Свои дни", callback_data="add:freq:custom"))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="add:cancel"))
    return builder.as_markup()


def custom_days_kb(selected: set[int], *, prefix: str = "add:day") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    row: list[InlineKeyboardButton] = []
    for i, label in enumerate(WEEKDAY_SHORT):
        mark = "●" if i in selected else "○"
        row.append(InlineKeyboardButton(text=f"{mark} {label}", callback_data=f"{prefix}:{i}"))
    builder.row(*row[:4])
    builder.row(*row[4:])
    builder.row(InlineKeyboardButton(text="✅ Готово", callback_data=f"{prefix}:done"))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="add:cancel"))
    return builder.as_markup()


def add_reminder_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Да", callback_data="add:rem:1"),
        InlineKeyboardButton(text="Нет", callback_data="add:rem:0"),
    )
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="add:cancel"))
    return builder.as_markup()


def add_confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Создать", callback_data="add:ok"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="add:cancel"),
    )
    return builder.as_markup()


def skip_value_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="add:cancel"))
    return builder.as_markup()
