from __future__ import annotations

from datetime import timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from keyboards.settings import stats_period_kb
from services.habit_service import HabitService
from services.statistics_service import StatisticsService
from utils.dates import local_today
from utils.formatters import escape, progress_bar, safe_edit

router = Router(name="statistics")


async def render_stats(
    target: Message,
    session: AsyncSession,
    user: User,
    period: int,
    *,
    edit: bool,
) -> None:
    period = period if period in {7, 30, 90} else 7
    today = local_today(user.settings.timezone if user.settings else "Europe/Moscow")
    service = HabitService(session)
    habits = await service.list_active(user.id)
    start = today - timedelta(days=max(period, 90) - 1)
    completions = await service.completions_in_range(user.id, start, today)
    overview = StatisticsService.overview(habits, completions, today, period)

    today_bar = progress_bar(overview.today_done, max(1, overview.today_scheduled))
    period_bar = progress_bar(overview.period.done, max(1, overview.period.scheduled))

    leaders = ""
    if overview.streak_leaders:
        parts = []
        for habit, current, best in overview.streak_leaders:
            if current <= 0 and best <= 0:
                continue
            parts.append(f"{habit.emoji} {escape(habit.name)} — 🔥 {current} / 🏆 {best}")
        if parts:
            leaders = "\n\n<b>Серии</b>\n" + "\n".join(parts[:5])

    text = (
        "<b>Статистика</b>\n\n"
        f"Сегодня: {today_bar} {overview.today_done}/{overview.today_scheduled}\n"
        f"{period} дней: {period_bar} {overview.period.done}/{overview.period.scheduled} "
        f"({overview.period.percent:.0f}%)\n\n"
        f"📋 Привычек: {overview.habits_count}\n"
        f"✅ Выполнений: {overview.completions_total}\n"
        f"🔥 Лучшая текущая серия: {overview.best_current_streak} дн.\n"
        f"🏆 Лучшая серия: {overview.best_best_streak} дн."
        f"{leaders}"
    )
    markup = stats_period_kb(period)
    if edit:
        await safe_edit(target, text, reply_markup=markup)
    else:
        await target.answer(text, parse_mode="HTML", reply_markup=markup)


@router.message(Command("stats"))
async def cmd_stats(message: Message, session: AsyncSession, db_user: User) -> None:
    await render_stats(message, session, db_user, 7, edit=False)


@router.callback_query(F.data == "menu:stats")
async def cb_stats(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    await callback.answer()
    await render_stats(callback.message, session, db_user, 7, edit=True)


@router.callback_query(F.data.startswith("st:"))
async def cb_stats_period(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    raw = callback.data.split(":")[-1]
    period = int(raw) if raw.isdigit() else 7
    await callback.answer()
    await render_stats(callback.message, session, db_user, period, edit=True)
