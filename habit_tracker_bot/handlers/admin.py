from __future__ import annotations

from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import Habit, HabitCompletion, User
from utils.formatters import safe_edit


def admin_home_kb() -> "InlineKeyboardMarkup":
    from aiogram.types import InlineKeyboardMarkup

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🌐 Lolzteam привычки", callback_data="alz:list"))
    builder.row(InlineKeyboardButton(text="↩️ В меню", callback_data="menu:main"))
    return builder.as_markup()

router = Router(name="admin")


def _is_admin(telegram_id: int) -> bool:
    return settings.admin_id is not None and telegram_id == settings.admin_id


@router.callback_query(F.data == "menu:admin")
async def admin_panel(callback: CallbackQuery, session: AsyncSession) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    active_since = now - timedelta(days=7)

    total_users = int(
        (await session.execute(select(func.count()).select_from(User))).scalar_one() or 0
    )
    active_users = int(
        (
            await session.execute(
                select(func.count()).select_from(User).where(User.last_activity_at >= active_since)
            )
        ).scalar_one()
        or 0
    )
    total_habits = int(
        (
            await session.execute(
                select(func.count()).select_from(Habit).where(Habit.is_active.is_(True))
            )
        ).scalar_one()
        or 0
    )
    total_completions = int(
        (await session.execute(select(func.count()).select_from(HabitCompletion))).scalar_one() or 0
    )
    reg_today = int(
        (
            await session.execute(
                select(func.count()).select_from(User).where(User.created_at >= day_ago)
            )
        ).scalar_one()
        or 0
    )
    reg_week = int(
        (
            await session.execute(
                select(func.count()).select_from(User).where(User.created_at >= week_ago)
            )
        ).scalar_one()
        or 0
    )

    text = (
        "<b>👑 Админ-панель</b>\n\n"
        f"👤 Всего пользователей: {total_users}\n"
        f"🟢 Активных за 7 дней: {active_users}\n"
        f"📋 Всего привычек: {total_habits}\n"
        f"✅ Всего выполнений: {total_completions}\n"
        f"📈 Регистрации за сутки: {reg_today}\n"
        f"📈 Регистрации за неделю: {reg_week}\n\n"
        "Содержимое привычек пользователей недоступно."
    )
    await callback.answer()
    await safe_edit(callback.message, text, reply_markup=admin_home_kb())
