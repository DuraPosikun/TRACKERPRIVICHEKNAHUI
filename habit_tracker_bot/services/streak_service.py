from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from database.models import Habit, HabitCompletion
from utils.dates import is_scheduled_on


@dataclass(slots=True)
class HabitStats:
    current_streak: int
    best_streak: int
    completions_count: int
    scheduled_count: int
    percent: float


class StreakService:
    @staticmethod
    def is_done(habit: Habit, completion: HabitCompletion | None) -> bool:
        if completion is None:
            return False
        return completion.value >= max(1, habit.target)

    @staticmethod
    def current_streak(
        habit: Habit,
        completions: dict[date, HabitCompletion],
        today: date,
    ) -> int:
        streak = 0
        cursor = today
        # If today is scheduled and not done, start from yesterday.
        if is_scheduled_on(habit.frequency, today) and not StreakService.is_done(
            habit, completions.get(today)
        ):
            cursor = today - timedelta(days=1)

        safety = 0
        while safety < 4000:
            safety += 1
            if cursor < habit.created_at.date():
                break
            if not is_scheduled_on(habit.frequency, cursor):
                cursor -= timedelta(days=1)
                continue
            if StreakService.is_done(habit, completions.get(cursor)):
                streak += 1
                cursor -= timedelta(days=1)
                continue
            break
        return streak

    @staticmethod
    def best_streak(
        habit: Habit,
        completions: dict[date, HabitCompletion],
        today: date,
    ) -> int:
        start = habit.created_at.date()
        if start > today:
            return 0
        best = 0
        current = 0
        cursor = start
        while cursor <= today:
            if is_scheduled_on(habit.frequency, cursor):
                if StreakService.is_done(habit, completions.get(cursor)):
                    current += 1
                    if current > best:
                        best = current
                else:
                    # today not done yet does not reset historical best mid-day
                    if cursor == today:
                        pass
                    else:
                        current = 0
            cursor += timedelta(days=1)
        return max(best, current)

    @staticmethod
    def stats(
        habit: Habit,
        completions: list[HabitCompletion],
        today: date,
    ) -> HabitStats:
        by_date = {c.date: c for c in completions}
        done_count = sum(1 for c in completions if StreakService.is_done(habit, c))
        start = habit.created_at.date()
        scheduled = 0
        cursor = start
        while cursor <= today:
            if is_scheduled_on(habit.frequency, cursor):
                scheduled += 1
            cursor += timedelta(days=1)
        percent = (done_count / scheduled * 100) if scheduled else 0.0
        return HabitStats(
            current_streak=StreakService.current_streak(habit, by_date, today),
            best_streak=StreakService.best_streak(habit, by_date, today),
            completions_count=done_count,
            scheduled_count=scheduled,
            percent=percent,
        )
