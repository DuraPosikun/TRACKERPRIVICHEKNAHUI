from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from keyboards.main import main_menu_kb
from keyboards.settings import delete_confirm_kb, settings_kb, timezone_kb
from handlers.common import is_admin
from services.user_service import delete_user_data
from utils.formatters import safe_edit
from utils.timezones import timezone_by_index, timezone_label

router = Router(name="settings")


async def render_settings(target: Message, user: User, *, edit: bool) -> None:
    settings_obj = user.settings
    if settings_obj is None:
        text = "Настройки ещё не созданы. Нажмите /start."
        if edit:
            await safe_edit(target, text, reply_markup=main_menu_kb(is_admin=is_admin(user.telegram_id)))
        else:
            await target.answer(text)
        return
    text = (
        "<b>Настройки</b>\n\n"
        f"🌍 Часовой пояс: {timezone_label(settings_obj.timezone)}\n"
        f"🔔 Уведомления: {'включены' if settings_obj.notifications_enabled else 'выключены'}\n"
        f"🕐 Формат времени: {'24 часа' if settings_obj.time_format == '24' else '12 часов'}"
    )
    if edit:
        await safe_edit(target, text, reply_markup=settings_kb(settings_obj))
    else:
        await target.answer(text, parse_mode="HTML", reply_markup=settings_kb(settings_obj))


@router.message(Command("settings"))
async def cmd_settings(message: Message, db_user: User) -> None:
    await render_settings(message, db_user, edit=False)


@router.callback_query(F.data == "menu:settings")
async def cb_settings(callback: CallbackQuery, db_user: User, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    await render_settings(callback.message, db_user, edit=True)


@router.callback_query(F.data == "set:notif")
async def toggle_notif(callback: CallbackQuery, db_user: User) -> None:
    if db_user.settings is None:
        await callback.answer("Нет настроек", show_alert=True)
        return
    db_user.settings.notifications_enabled = not db_user.settings.notifications_enabled
    await callback.answer("Сохранено")
    await render_settings(callback.message, db_user, edit=True)


@router.callback_query(F.data == "set:fmt")
async def toggle_fmt(callback: CallbackQuery, db_user: User) -> None:
    if db_user.settings is None:
        await callback.answer("Нет настроек", show_alert=True)
        return
    db_user.settings.time_format = "12" if db_user.settings.time_format == "24" else "24"
    await callback.answer("Сохранено")
    await render_settings(callback.message, db_user, edit=True)


@router.callback_query(F.data.startswith("set:tz:"))
async def tz_page(callback: CallbackQuery) -> None:
    raw = callback.data.split(":")[-1]
    page = int(raw) if raw.isdigit() else 0
    await callback.answer()
    await safe_edit(
        callback.message,
        "Выберите часовой пояс:",
        reply_markup=timezone_kb(page),
    )


@router.callback_query(F.data.startswith("set:tzs:"))
async def tz_set(callback: CallbackQuery, db_user: User) -> None:
    raw = callback.data.split(":")[-1]
    idx = int(raw) if raw.isdigit() else -1
    name = timezone_by_index(idx)
    if name is None or db_user.settings is None:
        await callback.answer("Некорректный пояс", show_alert=True)
        return
    db_user.settings.timezone = name
    await callback.answer(timezone_label(name))
    await render_settings(callback.message, db_user, edit=True)


@router.callback_query(F.data == "set:wipe")
async def wipe_ask(callback: CallbackQuery) -> None:
    await callback.answer()
    await safe_edit(
        callback.message,
        "Удалить все ваши данные безвозвратно?\n"
        "Привычки, отметки, статистика и настройки будут стерты.",
        reply_markup=delete_confirm_kb(),
    )


@router.callback_query(F.data == "set:wipe:yes")
async def wipe_yes(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
    state: FSMContext,
) -> None:
    await state.clear()
    await delete_user_data(session, db_user)
    await callback.answer("Данные удалены")
    await safe_edit(
        callback.message,
        "Ваши данные удалены. Нажмите /start, чтобы начать заново.",
        reply_markup=None,
    )
