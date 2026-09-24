from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import LolzCompletion, LolzTemplate, LolzUserHabit, User
from services.lolz_catalog import DEFAULT_TEMPLATES, FREQ_PRESETS
from utils.dates import is_scheduled_on


class LolzService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def seed_templates(self) -> None:
        existing = {
            row[0]
            for row in (
                await self.session.execute(select(LolzTemplate.code))
            ).all()
        }
        for item in DEFAULT_TEMPLATES:
            if item["code"] in existing:
                continue
            self.session.add(
                LolzTemplate(
                    code=item["code"],
                    title=item["title"],
                    description=item.get("description"),
                    emoji=item["emoji"],
                    category=item["category"],
                    recommended_frequency=item["recommended_frequency"],
                    is_active=True,
                    sort_order=int(item.get("sort_order") or 0),
                )
            )
        await self.session.flush()

    async def list_templates(self, *, active_only: bool = True) -> list[LolzTemplate]:
        stmt = select(LolzTemplate).order_by(LolzTemplate.sort_order.asc(), LolzTemplate.id.asc())
        if active_only:
            stmt = stmt.where(LolzTemplate.is_active.is_(True))
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_template(self, template_id: int) -> LolzTemplate | None:
        return await self.session.get(LolzTemplate, template_id)

    async def list_user_habits(self, user_id: int, *, active_only: bool = True) -> list[LolzUserHabit]:
        stmt = (
            select(LolzUserHabit)
            .where(LolzUserHabit.user_id == user_id)
            .order_by(LolzUserHabit.created_at.asc())
        )
        if active_only:
            stmt = stmt.where(LolzUserHabit.is_active.is_(True))
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_owned(self, habit_id: int, user_id: int) -> LolzUserHabit | None:
        result = await self.session.execute(
            select(LolzUserHabit).where(
                LolzUserHabit.id == habit_id,
                LolzUserHabit.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def activate_template(self, user: User, template: LolzTemplate) -> LolzUserHabit:
        result = await self.session.execute(
            select(LolzUserHabit).where(
                LolzUserHabit.user_id == user.id,
                LolzUserHabit.template_id == template.id,
            )
        )
        existing = result.scalar_one_or_none()
        freq = FREQ_PRESETS.get(template.recommended_frequency, "daily")
        if existing is not None:
            existing.is_active = True
            existing.title = template.title
            existing.emoji = template.emoji
            existing.description = template.description
            existing.category = template.category
            if not existing.frequency:
                existing.frequency = freq
            await self.session.flush()
            return existing
        habit = LolzUserHabit(
            user_id=user.id,
            template_id=template.id,
            title=template.title,
            emoji=template.emoji,
            description=template.description,
            category=template.category,
            frequency=freq,
            is_active=True,
        )
        self.session.add(habit)
        await self.session.flush()
        return habit

    async def create_custom(
        self,
        user: User,
        *,
        title: str,
        emoji: str,
        frequency: str,
        description: str | None = None,
    ) -> LolzUserHabit:
        habit = LolzUserHabit(
            user_id=user.id,
            template_id=None,
            title=title.strip()[:80],
            emoji=(emoji or "🌐").strip()[:16],
            description=(description.strip()[:500] if description else None),
            category="custom",
            frequency=frequency,
            is_active=True,
        )
        self.session.add(habit)
        await self.session.flush()
        return habit

    async def set_frequency(self, habit: LolzUserHabit, preset: str) -> None:
        habit.frequency = FREQ_PRESETS.get(preset, "daily")
        await self.session.flush()

    async def deactivate(self, habit: LolzUserHabit) -> None:
        habit.is_active = False
        await self.session.flush()

    async def delete_owned(self, habit: LolzUserHabit) -> None:
        await self.session.execute(
            delete(LolzCompletion).where(LolzCompletion.user_habit_id == habit.id)
        )
        await self.session.delete(habit)
        await self.session.flush()

    async def get_completion(
        self, habit_id: int, user_id: int, day: date
    ) -> LolzCompletion | None:
        result = await self.session.execute(
            select(LolzCompletion).where(
                LolzCompletion.user_habit_id == habit_id,
                LolzCompletion.user_id == user_id,
                LolzCompletion.date == day,
            )
        )
        return result.scalar_one_or_none()

    async def completions_on(self, user_id: int, day: date) -> dict[int, LolzCompletion]:
        result = await self.session.execute(
            select(LolzCompletion).where(
                LolzCompletion.user_id == user_id,
                LolzCompletion.date == day,
            )
        )
        return {row.user_habit_id: row for row in result.scalars().all()}

    async def completions_in_range(
        self, user_id: int, start: date, end: date
    ) -> list[LolzCompletion]:
        result = await self.session.execute(
            select(LolzCompletion).where(
                LolzCompletion.user_id == user_id,
                LolzCompletion.date >= start,
                LolzCompletion.date <= end,
            )
        )
        return list(result.scalars().all())

    async def toggle(self, habit: LolzUserHabit, day: date) -> LolzCompletion | None:
        existing = await self.get_completion(habit.id, habit.user_id, day)
        if existing is not None:
            await self.session.delete(existing)
            await self.session.flush()
            return None
        row = LolzCompletion(
            user_habit_id=habit.id,
            user_id=habit.user_id,
            date=day,
            value=1,
            completed_at=datetime.now(timezone.utc),
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def create_template(
        self,
        *,
        title: str,
        emoji: str,
        category: str,
        recommended_frequency: str,
        description: str | None,
    ) -> LolzTemplate:
        code = f"custom_{int(datetime.now(timezone.utc).timestamp())}"
        item = LolzTemplate(
            code=code,
            title=title.strip()[:80],
            emoji=(emoji or "🌐").strip()[:16],
            category=category,
            recommended_frequency=recommended_frequency,
            description=(description.strip()[:500] if description else None),
            is_active=True,
            sort_order=1000,
        )
        self.session.add(item)
        await self.session.flush()
        return item

    async def update_template(self, template: LolzTemplate, **fields: object) -> LolzTemplate:
        allowed = {
            "title",
            "emoji",
            "description",
            "category",
            "recommended_frequency",
            "is_active",
            "sort_order",
        }
        for key, value in fields.items():
            if key in allowed:
                setattr(template, key, value)
        await self.session.flush()
        return template

    async def delete_template(self, template: LolzTemplate) -> None:
        await self.session.delete(template)
        await self.session.flush()


@dataclass(slots=True)
class LolzOverview:
    today_done: int
    today_scheduled: int
    week_done: int
    month_done: int
    current_streak: int
    best_streak: int
    total_done: int
    top_habit: str | None


def _day_success(
    habits: list[LolzUserHabit],
    by_habit_date: dict[tuple[int, date], bool],
    day: date,
) -> str:
    planned = [
        h
        for h in habits
        if h.created_at.date() <= day and is_scheduled_on(h.frequency, day)
    ]
    if not planned:
        return "skip"
    if all(by_habit_date.get((h.id, day), False) for h in planned):
        return "ok"
    return "miss"


def lolz_overview(
    habits: list[LolzUserHabit],
    completions: list[LolzCompletion],
    today: date,
) -> LolzOverview:
    done_pairs = {(c.user_habit_id, c.date) for c in completions}
    flags = {pair: True for pair in done_pairs}

    today_planned = [
        h for h in habits if is_scheduled_on(h.frequency, today) and h.created_at.date() <= today
    ]
    today_done = sum(1 for h in today_planned if (h.id, today) in done_pairs)

    week_start = today - timedelta(days=6)
    month_start = today - timedelta(days=29)
    week_done = sum(1 for c in completions if week_start <= c.date <= today)
    month_done = sum(1 for c in completions if month_start <= c.date <= today)

    start = min((h.created_at.date() for h in habits), default=today)
    cursor = start
    current = 0
    best = 0
    running = 0
    while cursor <= today:
        status = _day_success(habits, flags, cursor)
        if status == "skip":
            cursor += timedelta(days=1)
            continue
        if status == "ok":
            running += 1
            best = max(best, running)
        else:
            if cursor == today:
                pass
            else:
                running = 0
        cursor += timedelta(days=1)
    current = running
    if _day_success(habits, flags, today) == "miss":
        # текущая серия без сегодняшнего незакрытого дня
        current = 0
        cursor = today - timedelta(days=1)
        acc = 0
        while cursor >= start:
            status = _day_success(habits, flags, cursor)
            if status == "skip":
                cursor -= timedelta(days=1)
                continue
            if status == "ok":
                acc += 1
                cursor -= timedelta(days=1)
                continue
            break
        current = acc

    names = Counter()
    by_id = {h.id: h for h in habits}
    for c in completions:
        habit = by_id.get(c.user_habit_id)
        if habit:
            names[f"{habit.emoji} {habit.title}"] += 1
    top = names.most_common(1)[0][0] if names else None

    return LolzOverview(
        today_done=today_done,
        today_scheduled=len(today_planned),
        week_done=week_done,
        month_done=month_done,
        current_streak=current,
        best_streak=best,
        total_done=len(completions),
        top_habit=top,
    )
