from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from database.models import Habit, HabitCompletion
from services.streak_service import StreakService
from utils.dates import is_scheduled_on


@dataclass(slots=True)
class PeriodStats:
    days: int
    scheduled: int
    done: int
    percent: float


@dataclass(slots=True)
class OverviewStats:
    habits_count: int
    completions_total: int
    today_done: int
    today_scheduled: int
    period: PeriodStats
    best_current_streak: int
    best_best_streak: int
    streak_leaders: list[tuple[Habit, int, int]]


class StatisticsService:
    @staticmethod
    def period_stats(
        habits: list[Habit],
        completions: list[HabitCompletion],
        today: date,
        days: int,
    ) -> PeriodStats:
        start = today - timedelta(days=days - 1)
        by_habit: dict[int, dict[date, HabitCompletion]] = defaultdict(dict)
        for c in completions:
            if start <= c.date <= today:
                by_habit[c.habit_id][c.date] = c

        scheduled = 0
        done = 0
        for habit in habits:
            created = habit.created_at.date()
            cursor = max(start, created)
            while cursor <= today:
                if is_scheduled_on(habit.frequency, cursor):
                    scheduled += 1
                    if StreakService.is_done(habit, by_habit[habit.id].get(cursor)):
                        done += 1
                cursor += timedelta(days=1)
        percent = (done / scheduled * 100) if scheduled else 0.0
        return PeriodStats(days=days, scheduled=scheduled, done=done, percent=percent)

    @staticmethod
    def day_status(
        habits: list[Habit],
        completions: list[HabitCompletion],
        day: date,
    ) -> str:
        """Return green / yellow / red / empty."""
        planned = [h for h in habits if h.created_at.date() <= day and is_scheduled_on(h.frequency, day)]
        if not planned:
            return "empty"
        by_habit = {c.habit_id: c for c in completions if c.date == day}
        done = sum(1 for h in planned if StreakService.is_done(h, by_habit.get(h.id)))
        if done == len(planned):
            return "green"
        if done == 0:
            return "red"
        return "yellow"

    @staticmethod
    def overview(
        habits: list[Habit],
        completions: list[HabitCompletion],
        today: date,
        period_days: int,
    ) -> OverviewStats:
        today_stats = StatisticsService.period_stats(habits, completions, today, 1)
        period = StatisticsService.period_stats(habits, completions, today, period_days)

        by_habit: dict[int, list[HabitCompletion]] = defaultdict(list)
        for c in completions:
            by_habit[c.habit_id].append(c)

        leaders: list[tuple[Habit, int, int]] = []
        best_current = 0
        best_best = 0
        for habit in habits:
            stats = StreakService.stats(habit, by_habit[habit.id], today)
            leaders.append((habit, stats.current_streak, stats.best_streak))
            best_current = max(best_current, stats.current_streak)
            best_best = max(best_best, stats.best_streak)
        leaders.sort(key=lambda x: x[1], reverse=True)

        return OverviewStats(
            habits_count=len(habits),
            completions_total=sum(
                1
                for h in habits
                for c in by_habit[h.id]
                if StreakService.is_done(h, c)
            ),
            today_done=today_stats.done,
            today_scheduled=today_stats.scheduled,
            period=period,
            best_current_streak=best_current,
            best_best_streak=best_best,
            streak_leaders=leaders[:5],
        )
