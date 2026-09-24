from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb(*, is_admin: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📋 Мои привычки", callback_data="menu:habits"))
    builder.row(InlineKeyboardButton(text="🌐 Lolzteam привычка", callback_data="menu:lolz"))
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="menu:stats"),
        InlineKeyboardButton(text="📅 Календарь", callback_data="menu:calendar"),
    )
    builder.row(InlineKeyboardButton(text="➕ Добавить привычку", callback_data="menu:add"))
    builder.row(
        InlineKeyboardButton(text="👤 Профиль", callback_data="menu:profile"),
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu:settings"),
    )
    builder.row(InlineKeyboardButton(text="ℹ️ О боте", callback_data="menu:about"))
    if is_admin:
        builder.row(InlineKeyboardButton(text="👑 Админ-панель", callback_data="menu:admin"))
    return builder.as_markup()


def about_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="↩️ В меню", callback_data="menu:main"))
    return builder.as_markup()


def back_menu_kb() -> InlineKeyboardMarkup:
    return about_kb()
