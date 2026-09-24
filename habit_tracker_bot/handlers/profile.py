from __future__ import annotations

from datetime import timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from keyboards.main import about_kb
from services.habit_service import HabitService
from services.statistics_service import StatisticsService
from utils.dates import format_date_short, local_today
from utils.formatters import escape, safe_edit

router = Router(name="profile")


async def render_profile(
    target: Message,
    session: AsyncSession,
    user: User,
    *,
    edit: bool,
) -> None:
    today = local_today(user.settings.timezone if user.settings else "Europe/Moscow")
    service = HabitService(session)
    habits = await service.list_active(user.id)
    start = min((h.created_at.date() for h in habits), default=today) if habits else today
    start = min(start, today - timedelta(days=365))
    completions = await service.completions_in_range(user.id, start, today)
    overview = StatisticsService.overview(habits, completions, today, 30)

    username = f"@{user.username}" if user.username else "—"
    name = escape(user.first_name or "Пользователь")
    text = (
        "<b>Профиль</b>\n\n"
        f"Имя: {name}\n"
        f"{username}\n\n"
        f"📅 С нами с: {format_date_short(user.created_at.date())}\n"
        f"📋 Привычек: {overview.habits_count}\n"
        f"✅ Выполнений: {overview.completions_total}\n"
        f"🔥 Текущая общая серия: {overview.best_current_streak} дн."
    )
    if edit:
        await safe_edit(target, text, reply_markup=about_kb())
    else:
        await target.answer(text, parse_mode="HTML", reply_markup=about_kb())


@router.message(Command("profile"))
async def cmd_profile(message: Message, session: AsyncSession, db_user: User) -> None:
    await render_profile(message, session, db_user, edit=False)


@router.callback_query(F.data == "menu:profile")
async def cb_profile(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    await callback.answer()
    await render_profile(callback.message, session, db_user, edit=True)
