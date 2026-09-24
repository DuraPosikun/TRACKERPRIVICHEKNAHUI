from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.common import is_admin
from keyboards.main import about_kb, main_menu_kb
from services.user_service import get_or_create_user
from utils.formatters import safe_edit

router = Router(name="start")


def welcome_text(first_name: str | None, is_new: bool) -> str:
    name = first_name or "друг"
    if is_new:
        return (
            f"Привет, {name}!\n\n"
            "Это трекер привычек. Каждый пользователь ведёт свои привычки отдельно.\n\n"
            "Добавь первую привычку и отмечай выполнение каждый день."
        )
    return f"Снова привет, {name}!\n\nВыбери раздел:"


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    tg = message.from_user
    _user, created = await get_or_create_user(
        session,
        telegram_id=tg.id,
        username=tg.username,
        first_name=tg.first_name,
    )
    await message.answer(
        welcome_text(tg.first_name, created),
        reply_markup=main_menu_kb(is_admin=is_admin(tg.id)),
    )


@router.callback_query(F.data == "menu:main")
async def cb_main(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    await safe_edit(
        callback.message,
        "Главное меню",
        reply_markup=main_menu_kb(is_admin=is_admin(callback.from_user.id)),
    )


@router.callback_query(F.data == "menu:about")
async def cb_about(callback: CallbackQuery) -> None:
    await callback.answer()
    await safe_edit(
        callback.message,
        "<b>О боте</b>\n\n"
        "Многопользовательский трекер привычек.\n"
        "Данные каждого аккаунта изолированы по Telegram ID.\n\n"
        "Можно добавлять привычки, отмечать выполнение, "
        "смотреть серии, статистику и календарь, получать напоминания "
        "в своём часовом поясе.\n\n"
        "Отдельный раздел «Lolzteam привычка» помогает отмечать "
        "социальную активность на форуме вручную. Бот не пишет на форум.",
        reply_markup=about_kb(),
    )


# Команды /habits /stats /profile /settings объявлены в своих роутерах.
