from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import Settings
from utils.timezones import TIMEZONES


def settings_kb(user_settings: Settings) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    notif = "вкл" if user_settings.notifications_enabled else "выкл"
    builder.row(
        InlineKeyboardButton(
            text=f"🔔 Уведомления: {notif}",
            callback_data="set:notif",
        )
    )
    builder.row(InlineKeyboardButton(text="🌍 Часовой пояс", callback_data="set:tz:0"))
    fmt = "24 ч" if user_settings.time_format == "24" else "12 ч"
    builder.row(InlineKeyboardButton(text=f"🕐 Формат времени: {fmt}", callback_data="set:fmt"))
    builder.row(InlineKeyboardButton(text="🗑 Удалить мои данные", callback_data="set:wipe"))
    builder.row(InlineKeyboardButton(text="↩️ Меню", callback_data="menu:main"))
    return builder.as_markup()


def timezone_kb(page: int, per_page: int = 8) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    start = page * per_page
    chunk = TIMEZONES[start : start + per_page]
    for idx, (_name, city, offset) in enumerate(chunk, start=start):
        builder.row(
            InlineKeyboardButton(
                text=f"{city} {offset}",
                callback_data=f"set:tzs:{idx}",
            )
        )
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"set:tz:{page - 1}"))
    if start + per_page < len(TIMEZONES):
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"set:tz:{page + 1}"))
    if nav:
        builder.row(*nav)
    builder.row(InlineKeyboardButton(text="↩️ Настройки", callback_data="menu:settings"))
    return builder.as_markup()


def time_format_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="24 часа", callback_data="set:fmt:24"),
        InlineKeyboardButton(text="12 часов", callback_data="set:fmt:12"),
    )
    builder.row(InlineKeyboardButton(text="↩️ Настройки", callback_data="menu:settings"))
    return builder.as_markup()


def delete_confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌ Да, удалить всё", callback_data="set:wipe:yes"),
        InlineKeyboardButton(text="↩️ Отмена", callback_data="menu:settings"),
    )
    return builder.as_markup()


def stats_period_kb(current: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    buttons = []
    for days in (7, 30, 90):
        prefix = "• " if days == current else ""
        buttons.append(InlineKeyboardButton(text=f"{prefix}{days} дн.", callback_data=f"st:{days}"))
    builder.row(*buttons)
    builder.row(InlineKeyboardButton(text="↩️ Меню", callback_data="menu:main"))
    return builder.as_markup()
