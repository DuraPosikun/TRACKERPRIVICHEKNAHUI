from __future__ import annotations

from datetime import date, datetime, time, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    habits: Mapped[list[Habit]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    settings: Mapped[Settings | None] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    completions: Mapped[list[HabitCompletion]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    lolz_habits: Mapped[list["LolzUserHabit"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    lolz_completions: Mapped[list["LolzCompletion"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Settings(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Europe/Moscow")
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    time_format: Mapped[str] = mapped_column(String(8), nullable=False, default="24")

    user: Mapped[User] = relationship(back_populates="settings")


class Habit(Base):
    __tablename__ = "habits"
    __table_args__ = (
        Index("ix_habits_user_active", "user_id", "is_active"),
        Index("ix_habits_reminder", "reminder_enabled", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    emoji: Mapped[str] = mapped_column(String(16), nullable=False, default="✅")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    frequency: Mapped[str] = mapped_column(String(32), nullable=False, default="daily")
    target: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    reminder_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reminder_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    last_reminder_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped[User] = relationship(back_populates="habits")
    completions: Mapped[list[HabitCompletion]] = relationship(
        back_populates="habit",
        cascade="all, delete-orphan",
    )


class HabitCompletion(Base):
    __tablename__ = "habit_completions"
    __table_args__ = (
        UniqueConstraint("habit_id", "date", name="uq_completion_habit_date"),
        Index("ix_completions_user_date", "user_id", "date"),
        Index("ix_completions_habit_date", "habit_id", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    habit_id: Mapped[int] = mapped_column(
        ForeignKey("habits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    habit: Mapped[Habit] = relationship(back_populates="completions")
    user: Mapped[User] = relationship(back_populates="completions")


class LolzTemplate(Base):
    __tablename__ = "lolzteam_habit_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    emoji: Mapped[str] = mapped_column(String(16), nullable=False, default="🌐")
    category: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    recommended_frequency: Mapped[str] = mapped_column(String(16), nullable=False, default="daily")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    user_habits: Mapped[list["LolzUserHabit"]] = relationship(back_populates="template")


class LolzUserHabit(Base):
    __tablename__ = "lolzteam_user_habits"
    __table_args__ = (
        UniqueConstraint("user_id", "template_id", name="uq_lolz_user_template"),
        Index("ix_lolz_user_active", "user_id", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    template_id: Mapped[int | None] = mapped_column(
        ForeignKey("lolzteam_habit_templates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(80), nullable=False)
    emoji: Mapped[str] = mapped_column(String(16), nullable=False, default="🌐")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(24), nullable=False, default="custom")
    frequency: Mapped[str] = mapped_column(String(32), nullable=False, default="daily")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="lolz_habits")
    template: Mapped[LolzTemplate | None] = relationship(back_populates="user_habits")
    completions: Mapped[list["LolzCompletion"]] = relationship(
        back_populates="user_habit",
        cascade="all, delete-orphan",
    )


class LolzCompletion(Base):
    __tablename__ = "lolzteam_completions"
    __table_args__ = (
        UniqueConstraint("user_habit_id", "date", name="uq_lolz_completion_day"),
        Index("ix_lolz_comp_user_date", "user_id", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_habit_id: Mapped[int] = mapped_column(
        ForeignKey("lolzteam_user_habits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    user_habit: Mapped[LolzUserHabit] = relationship(back_populates="completions")
    user: Mapped[User] = relationship(back_populates="lolz_completions")
