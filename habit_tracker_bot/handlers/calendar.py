from __future__ import annotations

from datetime import date, timedelta

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from keyboards.calendar import calendar_kb, day_habits_kb
from services.habit_service import HabitService
from services.statistics_service import StatisticsService
from services.streak_service import StreakService
from utils.dates import MONTH_TITLES, format_date, is_scheduled_on, local_today
from utils.formatters import escape, progress_bar, safe_edit

router = Router(name="calendar")


def _clamp_month(year: int, month: int) -> tuple[int, int]:
    if month < 1:
        return year - 1, 12
    if month > 12:
        return year + 1, 1
    return year, month


async def render_calendar(
    callback: CallbackQuery,
    session: AsyncSession,
    user: User,
    year: int,
    month: int,
) -> None:
    today = local_today(user.settings.timezone if user.settings else "Europe/Moscow")
    year, month = _clamp_month(year, month)
    if year < 2020 or year > today.year + 1:
        year, month = today.year, today.month

    service = HabitService(session)
    habits = await service.list_active(user.id)
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)
    completions = await service.completions_in_range(user.id, start, end)

    statuses: dict[int, str] = {}
    cursor = start
    while cursor <= end:
        statuses[cursor.day] = StatisticsService.day_status(habits, completions, cursor)
        cursor += timedelta(days=1)

    text = (
        f"<b>Календарь — {MONTH_TITLES[month]} {year}</b>\n\n"
        "🟢 всё выполнено\n"
        "🟡 частично\n"
        "🔴 есть пропуски\n"
        "⚪ нет запланированных / нет данных"
    )
    await safe_edit(
        callback.message,
        text,
        reply_markup=calendar_kb(year, month, statuses, today),
    )


@router.callback_query(F.data == "menu:calendar")
async def cb_calendar(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    today = local_today(db_user.settings.timezone if db_user.settings else "Europe/Moscow")
    await callback.answer()
    await render_calendar(callback, session, db_user, today.year, today.month)


@router.callback_query(F.data.startswith("cal:m:"))
async def cb_calendar_month(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer()
        return
    try:
        year, month = int(parts[2]), int(parts[3])
    except ValueError:
        await callback.answer()
        return
    await callback.answer()
    await render_calendar(callback, session, db_user, year, month)


@router.callback_query(F.data.startswith("cal:d:"))
async def cb_calendar_day(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    parts = callback.data.split(":")
    if len(parts) != 5:
        await callback.answer()
        return
    try:
        year, month, day = int(parts[2]), int(parts[3]), int(parts[4])
        selected = date(year, month, day)
    except ValueError:
        await callback.answer("Некорректная дата", show_alert=True)
        return

    today = local_today(db_user.settings.timezone if db_user.settings else "Europe/Moscow")
    service = HabitService(session)
    habits = await service.list_active(db_user.id)
    planned = [
        h
        for h in habits
        if h.created_at.date() <= selected and is_scheduled_on(h.frequency, selected)
    ]
    completions = await service.completions_for_user_on(db_user.id, selected)

    lines = [f"<b>{format_date(selected)}</b>\n"]
    if selected > today:
        lines.append("Этот день ещё не наступил.")
    elif not planned:
        lines.append("Нет запланированных привычек.")
    else:
        for habit in planned:
            comp = completions.get(habit.id)
            done = StreakService.is_done(habit, comp)
            check = "☑️" if done else "⬜"
            value = comp.value if comp else 0
            if habit.target > 1:
                lines.append(
                    f"{check} {habit.emoji} {escape(habit.name)} "
                    f"{progress_bar(value, habit.target)} {value}/{habit.target}"
                )
            else:
                lines.append(f"{check} {habit.emoji} {escape(habit.name)}")
    await callback.answer()
    await safe_edit(
        callback.message,
        "\n".join(lines),
        reply_markup=day_habits_kb(year, month),
    )
