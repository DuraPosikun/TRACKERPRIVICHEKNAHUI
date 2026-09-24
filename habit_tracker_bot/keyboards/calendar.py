from __future__ import annotations

import calendar as pycal
from datetime import date

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.dates import MONTH_TITLES, WEEKDAY_SHORT

STATUS_ICON = {
    "green": "🟢",
    "yellow": "🟡",
    "red": "🔴",
    "empty": "⚪",
    "future": "·",
}


def calendar_kb(
    year: int,
    month: int,
    statuses: dict[int, str],
    today: date,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    title = f"{MONTH_TITLES[month]} {year}"
    builder.row(InlineKeyboardButton(text=title, callback_data="cal:noop"))
    builder.row(*[InlineKeyboardButton(text=n, callback_data="cal:noop") for n in WEEKDAY_SHORT])

    weeks = pycal.Calendar(firstweekday=0).monthdayscalendar(year, month)
    for week in weeks:
        row: list[InlineKeyboardButton] = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="cal:noop"))
                continue
            current = date(year, month, day)
            if current > today:
                icon = "·"
            else:
                icon = STATUS_ICON.get(statuses.get(day, "empty"), "⚪")
            row.append(
                InlineKeyboardButton(
                    text=f"{icon}{day}",
                    callback_data=f"cal:d:{year}:{month}:{day}",
                )
            )
        builder.row(*row)

    prev_y, prev_m = (year - 1, 12) if month == 1 else (year, month - 1)
    next_y, next_m = (year + 1, 1) if month == 12 else (year, month + 1)
    builder.row(
        InlineKeyboardButton(text="◀️", callback_data=f"cal:m:{prev_y}:{prev_m}"),
        InlineKeyboardButton(text="Сегодня", callback_data=f"cal:m:{today.year}:{today.month}"),
        InlineKeyboardButton(text="▶️", callback_data=f"cal:m:{next_y}:{next_m}"),
    )
    builder.row(InlineKeyboardButton(text="↩️ Меню", callback_data="menu:main"))
    return builder.as_markup()


def day_habits_kb(year: int, month: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="↩️ К календарю", callback_data=f"cal:m:{year}:{month}"))
    builder.row(InlineKeyboardButton(text="📋 Привычки", callback_data="menu:habits"))
    return builder.as_markup()
