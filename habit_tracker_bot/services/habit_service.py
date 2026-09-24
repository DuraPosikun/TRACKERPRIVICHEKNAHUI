from __future__ import annotations

from datetime import date, datetime, time, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import Habit, HabitCompletion, User


class HabitService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_active(self, user_id: int) -> list[Habit]:
        result = await self.session.execute(
            select(Habit)
            .where(Habit.user_id == user_id, Habit.is_active.is_(True))
            .order_by(Habit.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_owned(self, habit_id: int, user_id: int) -> Habit | None:
        result = await self.session.execute(
            select(Habit).where(Habit.id == habit_id, Habit.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        user: User,
        *,
        name: str,
        emoji: str,
        description: str | None,
        frequency: str,
        target: int,
        reminder_enabled: bool,
        reminder_time: time | None,
    ) -> Habit:
        habit = Habit(
            user_id=user.id,
            name=name.strip()[:64],
            emoji=(emoji or "✅").strip()[:16],
            description=(description.strip()[:500] if description else None),
            frequency=frequency,
            target=max(1, int(target)),
            reminder_enabled=bool(reminder_enabled),
            reminder_time=reminder_time,
            is_active=True,
        )
        self.session.add(habit)
        await self.session.flush()
        return habit

    async def update(self, habit: Habit, **fields: object) -> Habit:
        allowed = {
            "name",
            "emoji",
            "description",
            "frequency",
            "target",
            "reminder_enabled",
            "reminder_time",
            "is_active",
        }
        for key, value in fields.items():
            if key in allowed:
                setattr(habit, key, value)
        await self.session.flush()
        return habit

    async def delete_owned(self, habit: Habit) -> None:
        await self.session.execute(
            delete(HabitCompletion).where(HabitCompletion.habit_id == habit.id)
        )
        await self.session.delete(habit)
        await self.session.flush()

    async def get_completion(
        self, habit_id: int, user_id: int, day: date
    ) -> HabitCompletion | None:
        result = await self.session.execute(
            select(HabitCompletion).where(
                HabitCompletion.habit_id == habit_id,
                HabitCompletion.user_id == user_id,
                HabitCompletion.date == day,
            )
        )
        return result.scalar_one_or_none()

    async def completions_for_user_on(
        self, user_id: int, day: date
    ) -> dict[int, HabitCompletion]:
        result = await self.session.execute(
            select(HabitCompletion).where(
                HabitCompletion.user_id == user_id,
                HabitCompletion.date == day,
            )
        )
        return {row.habit_id: row for row in result.scalars().all()}

    async def completions_in_range(
        self, user_id: int, start: date, end: date
    ) -> list[HabitCompletion]:
        result = await self.session.execute(
            select(HabitCompletion).where(
                HabitCompletion.user_id == user_id,
                HabitCompletion.date >= start,
                HabitCompletion.date <= end,
            )
        )
        return list(result.scalars().all())

    async def habit_completions_in_range(
        self, habit_id: int, user_id: int, start: date, end: date
    ) -> list[HabitCompletion]:
        result = await self.session.execute(
            select(HabitCompletion).where(
                HabitCompletion.habit_id == habit_id,
                HabitCompletion.user_id == user_id,
                HabitCompletion.date >= start,
                HabitCompletion.date <= end,
            )
        )
        return list(result.scalars().all())

    async def toggle_binary(self, habit: Habit, day: date) -> HabitCompletion | None:
        existing = await self.get_completion(habit.id, habit.user_id, day)
        if existing is not None:
            await self.session.delete(existing)
            await self.session.flush()
            return None
        completion = HabitCompletion(
            habit_id=habit.id,
            user_id=habit.user_id,
            date=day,
            value=max(1, habit.target),
            completed_at=datetime.now(timezone.utc),
        )
        self.session.add(completion)
        await self.session.flush()
        return completion

    async def set_value(self, habit: Habit, day: date, value: int) -> HabitCompletion | None:
        value = max(0, int(value))
        existing = await self.get_completion(habit.id, habit.user_id, day)
        if value <= 0:
            if existing is not None:
                await self.session.delete(existing)
                await self.session.flush()
            return None
        if existing is None:
            existing = HabitCompletion(
                habit_id=habit.id,
                user_id=habit.user_id,
                date=day,
                value=value,
                completed_at=datetime.now(timezone.utc),
            )
            self.session.add(existing)
        else:
            existing.value = value
            existing.completed_at = datetime.now(timezone.utc)
        await self.session.flush()
        return existing

    async def increment(self, habit: Habit, day: date, delta: int = 1) -> HabitCompletion | None:
        existing = await self.get_completion(habit.id, habit.user_id, day)
        current = existing.value if existing else 0
        return await self.set_value(habit, day, current + delta)

    async def count_habits(self, user_id: int) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Habit).where(
                Habit.user_id == user_id, Habit.is_active.is_(True)
            )
        )
        return int(result.scalar_one() or 0)

    async def count_completions(self, user_id: int) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(HabitCompletion).where(
                HabitCompletion.user_id == user_id
            )
        )
        return int(result.scalar_one() or 0)

    async def load_with_completions(self, habit_id: int, user_id: int) -> Habit | None:
        result = await self.session.execute(
            select(Habit)
            .options(selectinload(Habit.completions))
            .where(Habit.id == habit_id, Habit.user_id == user_id)
        )
        return result.scalar_one_or_none()
