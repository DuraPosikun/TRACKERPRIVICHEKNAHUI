from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.filters import Command, ExceptionTypeFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ErrorEvent, Message
from sqlalchemy.exc import SQLAlchemyError

from config import settings
from keyboards.main import main_menu_kb

router = Router(name="common")
logger = logging.getLogger(__name__)


def is_admin(telegram_id: int) -> bool:
    return settings.admin_id is not None and telegram_id == settings.admin_id


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    await state.clear()
    if current is None:
        await message.answer(
            "Сейчас нечего отменять.",
            reply_markup=main_menu_kb(is_admin=is_admin(message.from_user.id)),
        )
        return
    await message.answer(
        "Действие отменено.",
        reply_markup=main_menu_kb(is_admin=is_admin(message.from_user.id)),
    )


@router.callback_query(F.data == "add:cancel")
async def cb_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer("Отменено")
    try:
        await callback.message.edit_text(
            "Действие отменено.",
            reply_markup=main_menu_kb(is_admin=is_admin(callback.from_user.id)),
        )
    except TelegramBadRequest:
        await callback.message.answer(
            "Действие отменено.",
            reply_markup=main_menu_kb(is_admin=is_admin(callback.from_user.id)),
        )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "<b>Помощь</b>\n\n"
        "Этот бот помогает вести привычки.\n\n"
        "📋 Мои привычки — список на сегодня и отметки\n"
        "➕ Добавить — мастер создания\n"
        "📊 Статистика — прогресс за период\n"
        "📅 Календарь — дни месяца\n"
        "👤 Профиль и ⚙️ Настройки\n\n"
        "Команды:\n"
        "/start — меню\n"
        "/habits — привычки\n"
        "/stats — статистика\n"
        "/profile — профиль\n"
        "/settings — настройки\n"
        "/cancel — отменить текущее действие\n"
        "/help — эта справка",
        parse_mode="HTML",
        reply_markup=main_menu_kb(is_admin=is_admin(message.from_user.id)),
    )


@router.callback_query(F.data == "cal:noop")
async def cb_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.errors(ExceptionTypeFilter(SQLAlchemyError))
async def on_db_error(event: ErrorEvent) -> None:
    logger.exception("Ошибка базы данных: %s", event.exception)
    update = event.update
    if update.message:
        await update.message.answer("Не получилось сохранить данные. Попробуйте ещё раз.")
    elif update.callback_query:
        await update.callback_query.answer("Ошибка базы данных", show_alert=True)


@router.errors(ExceptionTypeFilter(TelegramAPIError))
async def on_tg_error(event: ErrorEvent) -> None:
    logger.exception("Ошибка Telegram API: %s", event.exception)


@router.errors()
async def on_any_error(event: ErrorEvent) -> None:
    logger.exception("Необработанная ошибка: %s", event.exception)
    update = event.update
    try:
        if update.callback_query:
            await update.callback_query.answer("Произошла ошибка. Попробуйте ещё раз.", show_alert=True)
        elif update.message:
            await update.message.answer("Произошла ошибка. Попробуйте ещё раз.")
    except Exception:
        logger.warning("Не удалось отправить сообщение об ошибке")
