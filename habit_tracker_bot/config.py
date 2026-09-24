from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _parse_admin_id(raw: str) -> int | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    admin_id: int | None
    database_url: str
    default_timezone: str
    log_level: str


def load_settings() -> Settings:
    token = (os.getenv("BOT_TOKEN") or "").strip()
    if not token or token == "YOUR_BOT_TOKEN":
        raise RuntimeError(
            "BOT_TOKEN не задан. Скопируйте .env.example в .env и укажите токен бота."
        )

    db_url = (os.getenv("DATABASE_URL") or "sqlite+aiosqlite:///./data/habit_tracker.db").strip()
    tz = (os.getenv("DEFAULT_TIMEZONE") or "Europe/Moscow").strip()
    level = (os.getenv("LOG_LEVEL") or "INFO").strip().upper()

    return Settings(
        bot_token=token,
        admin_id=_parse_admin_id(os.getenv("ADMIN_ID") or ""),
        database_url=db_url,
        default_timezone=tz,
        log_level=level,
    )


settings = load_settings()


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
