from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import settings
from database.models import Settings, User, utcnow


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(
        select(User)
        .options(selectinload(User.settings), selectinload(User.habits))
        .where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    first_name: str | None,
) -> tuple[User, bool]:
    user = await get_user_by_telegram_id(session, telegram_id)
    if user is not None:
        user.username = username
        user.first_name = first_name
        user.last_activity_at = utcnow()
        if user.settings is None:
            session.add(
                Settings(
                    user_id=user.id,
                    timezone=settings.default_timezone,
                    notifications_enabled=True,
                    time_format="24",
                )
            )
            await session.flush()
            await session.refresh(user, attribute_names=["settings"])
        return user, False

    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        created_at=utcnow(),
        last_activity_at=utcnow(),
    )
    session.add(user)
    await session.flush()
    session.add(
        Settings(
            user_id=user.id,
            timezone=settings.default_timezone,
            notifications_enabled=True,
            time_format="24",
        )
    )
    await session.flush()
    await session.refresh(user, attribute_names=["settings"])
    return user, True


async def touch_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    first_name: str | None,
) -> User:
    user, _ = await get_or_create_user(session, telegram_id, username, first_name)
    return user


async def delete_user_data(session: AsyncSession, user: User) -> None:
    await session.delete(user)
    await session.flush()
