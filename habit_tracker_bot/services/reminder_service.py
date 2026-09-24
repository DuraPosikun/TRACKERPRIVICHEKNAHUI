from __future__ import annotations

import logging
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.database import SessionLocal
from database.models import Habit, Settings, User
from services.habit_service import HabitService
from services.streak_service import StreakService
from utils.dates import is_scheduled_on, local_now, local_today

logger = logging.getLogger(__name__)


class ReminderService:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone="UTC")

    def start(self) -> None:
        self.scheduler.add_job(
            self.tick,
            "interval",
            minutes=1,
            id="habit_reminders",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=30,
        )
        self.scheduler.start()
        logger.info("Планировщик напоминаний запущен")

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Планировщик напоминаний остановлен")

    async def tick(self) -> None:
        try:
            await self._process()
        except Exception:
            logger.exception("Ошибка при обработке напоминаний")

    async def _process(self) -> None:
        async with SessionLocal() as session:
            result = await session.execute(
                select(Habit)
                .options(selectinload(Habit.user).selectinload(User.settings))
                .join(User, User.id == Habit.user_id)
                .join(Settings, Settings.user_id == User.id)
                .where(
                    Habit.is_active.is_(True),
                    Habit.reminder_enabled.is_(True),
                    Habit.reminder_time.is_not(None),
                    Settings.notifications_enabled.is_(True),
                )
            )
            habits = list(result.scalars().all())
            if not habits:
                return

            service = HabitService(session)
            sent = 0
            for habit in habits:
                user = habit.user
                tz_name = user.settings.timezone if user.settings else "Europe/Moscow"
                now_local = local_now(tz_name)
                today = now_local.date()

                if habit.reminder_time is None:
                    continue
                if now_local.hour != habit.reminder_time.hour:
                    continue
                if now_local.minute != habit.reminder_time.minute:
                    continue
                if habit.last_reminder_date == today:
                    continue
                if not is_scheduled_on(habit.frequency, today):
                    continue
                if habit.created_at.replace(tzinfo=habit.created_at.tzinfo or timezone.utc).date() > today:
                    continue

                completion = await service.get_completion(habit.id, habit.user_id, today)
                if StreakService.is_done(habit, completion):
                    continue

                text = (
                    "🔔 <b>Напоминание!</b>\n\n"
                    "Ты ещё не выполнил:\n"
                    f"{habit.emoji} <b>{_escape(habit.name)}</b>\n\n"
                    "Не забудь выполнить её сегодня 💪"
                )
                try:
                    await self.bot.send_message(chat_id=user.telegram_id, text=text, parse_mode="HTML")
                    habit.last_reminder_date = today
                    sent += 1
                except TelegramForbiddenError:
                    logger.info("Пользователь %s заблокировал бота, уведомления отключены", user.telegram_id)
                    if user.settings:
                        user.settings.notifications_enabled = False
                except TelegramRetryAfter as exc:
                    logger.warning("Flood control: повтор через %s сек", exc.retry_after)
                    break
                except Exception:
                    logger.exception("Не удалось отправить напоминание user_id=%s habit_id=%s", user.id, habit.id)

            if sent:
                await session.commit()
                logger.info("Отправлено напоминаний: %s", sent)
            else:
                await session.commit()


def _escape(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
