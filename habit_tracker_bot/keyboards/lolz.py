from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import LolzTemplate, LolzUserHabit
from services.lolz_catalog import CATEGORIES, FREQ_LABELS


def lolz_home_kb(habits: list[LolzUserHabit], marks: dict[int, bool]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for habit in habits:
        check = "☑️" if marks.get(habit.id) else "⬜"
        builder.row(
            InlineKeyboardButton(
                text=f"{check} {habit.emoji} {habit.title}",
                callback_data=f"lz:v:{habit.id}",
            )
        )
    builder.row(InlineKeyboardButton(text="📊 Статистика", callback_data="lz:st"))
    builder.row(
        InlineKeyboardButton(text="➕ Добавить", callback_data="lz:add"),
        InlineKeyboardButton(text="⚙️ Мои привычки", callback_data="lz:mine"),
    )
    builder.row(InlineKeyboardButton(text="↩️ Меню", callback_data="menu:main"))
    return builder.as_markup()


def lolz_add_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, title in CATEGORIES.items():
        if code == "custom":
            continue
        builder.row(InlineKeyboardButton(text=title, callback_data=f"lz:cat:{code}"))
    builder.row(InlineKeyboardButton(text="➕ Своя привычка", callback_data="lz:custom"))
    builder.row(InlineKeyboardButton(text="↩️ Назад", callback_data="menu:lolz"))
    return builder.as_markup()


def lolz_templates_kb(templates: list[LolzTemplate], taken: set[int]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for tpl in templates:
        mark = "✓ " if tpl.id in taken else ""
        builder.row(
            InlineKeyboardButton(
                text=f"{mark}{tpl.emoji} {tpl.title}",
                callback_data=f"lz:tpl:{tpl.id}",
            )
        )
    builder.row(InlineKeyboardButton(text="↩️ Категории", callback_data="lz:add"))
    return builder.as_markup()


def lolz_template_kb(template_id: int, already: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if already:
        builder.row(InlineKeyboardButton(text="Уже в списке", callback_data="lz:add"))
    else:
        builder.row(InlineKeyboardButton(text="➕ Добавить себе", callback_data=f"lz:on:{template_id}"))
    builder.row(InlineKeyboardButton(text="↩️ Назад", callback_data="lz:add"))
    return builder.as_markup()


def lolz_habit_kb(habit: LolzUserHabit, *, done: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if done:
        builder.row(InlineKeyboardButton(text="☑️ Выполнено — снять", callback_data=f"lz:tg:{habit.id}"))
    else:
        builder.row(InlineKeyboardButton(text="⬜ Отметить выполнение", callback_data=f"lz:tg:{habit.id}"))
    builder.row(InlineKeyboardButton(text="📅 Периодичность", callback_data=f"lz:fr:{habit.id}"))
    builder.row(InlineKeyboardButton(text="🗑 Убрать из списка", callback_data=f"lz:rm:{habit.id}"))
    builder.row(InlineKeyboardButton(text="↩️ К разделу", callback_data="menu:lolz"))
    return builder.as_markup()


def lolz_freq_kb(habit_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Каждый день", callback_data=f"lz:fs:{habit_id}:daily"))
    builder.row(InlineKeyboardButton(text="Несколько раз в неделю", callback_data=f"lz:fs:{habit_id}:few"))
    builder.row(InlineKeyboardButton(text="Раз в неделю", callback_data=f"lz:fs:{habit_id}:weekly"))
    builder.row(InlineKeyboardButton(text="↩️ Назад", callback_data=f"lz:v:{habit_id}"))
    return builder.as_markup()


def lolz_mine_kb(habits: list[LolzUserHabit]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for habit in habits:
        builder.row(
            InlineKeyboardButton(
                text=f"{habit.emoji} {habit.title}",
                callback_data=f"lz:v:{habit.id}",
            )
        )
    builder.row(InlineKeyboardButton(text="↩️ Назад", callback_data="menu:lolz"))
    return builder.as_markup()


def lolz_stats_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="↩️ К разделу", callback_data="menu:lolz"))
    return builder.as_markup()


def lolz_custom_cancel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="lz:cancel"))
    return builder.as_markup()


def lolz_custom_freq_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Каждый день", callback_data="lz:cf:daily"))
    builder.row(InlineKeyboardButton(text="Несколько раз в неделю", callback_data="lz:cf:few"))
    builder.row(InlineKeyboardButton(text="Раз в неделю", callback_data="lz:cf:weekly"))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="lz:cancel"))
    return builder.as_markup()


def admin_lolz_list_kb(templates: list[LolzTemplate]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for tpl in templates:
        flag = "🟢" if tpl.is_active else "⚪"
        builder.row(
            InlineKeyboardButton(
                text=f"{flag} {tpl.emoji} {tpl.title}",
                callback_data=f"alz:v:{tpl.id}",
            )
        )
    builder.row(InlineKeyboardButton(text="➕ Новый шаблон", callback_data="alz:new"))
    builder.row(InlineKeyboardButton(text="↩️ Админка", callback_data="menu:admin"))
    return builder.as_markup()


def admin_lolz_item_kb(template: LolzTemplate) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    toggle = "Отключить" if template.is_active else "Включить"
    builder.row(InlineKeyboardButton(text=toggle, callback_data=f"alz:tg:{template.id}"))
    builder.row(InlineKeyboardButton(text="Категория", callback_data=f"alz:cat:{template.id}"))
    builder.row(InlineKeyboardButton(text="Периодичность", callback_data=f"alz:fr:{template.id}"))
    builder.row(InlineKeyboardButton(text="Переименовать", callback_data=f"alz:ren:{template.id}"))
    builder.row(InlineKeyboardButton(text="🗑 Удалить шаблон", callback_data=f"alz:dl:{template.id}"))
    builder.row(InlineKeyboardButton(text="↩️ Список", callback_data="alz:list"))
    return builder.as_markup()


def admin_lolz_cats_kb(template_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, title in CATEGORIES.items():
        if code == "custom":
            continue
        builder.row(InlineKeyboardButton(text=title, callback_data=f"alz:cs:{template_id}:{code}"))
    builder.row(InlineKeyboardButton(text="↩️ Назад", callback_data=f"alz:v:{template_id}"))
    return builder.as_markup()


def admin_lolz_freq_kb(template_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, title in FREQ_LABELS.items():
        builder.row(InlineKeyboardButton(text=title, callback_data=f"alz:fs:{template_id}:{code}"))
    builder.row(InlineKeyboardButton(text="↩️ Назад", callback_data=f"alz:v:{template_id}"))
    return builder.as_markup()


def admin_lolz_delete_kb(template_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌ Да, удалить", callback_data=f"alz:dx:{template_id}"),
        InlineKeyboardButton(text="↩️ Отмена", callback_data=f"alz:v:{template_id}"),
    )
    return builder.as_markup()


def admin_lolz_cancel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="alz:list"))
    return builder.as_markup()


def admin_lolz_new_cats_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, title in CATEGORIES.items():
        if code == "custom":
            continue
        builder.row(InlineKeyboardButton(text=title, callback_data=f"alz:nc:{code}"))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="alz:list"))
    return builder.as_markup()


def admin_lolz_new_freq_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, title in FREQ_LABELS.items():
        builder.row(InlineKeyboardButton(text=title, callback_data=f"alz:nf:{code}"))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="alz:list"))
    return builder.as_markup()
