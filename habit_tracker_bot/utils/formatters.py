from __future__ import annotations

import logging
from typing import Any

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, Message

logger = logging.getLogger(__name__)


def progress_bar(current: int, target: int, width: int = 8) -> str:
    if target <= 0:
        target = 1
    current = max(0, current)
    filled = min(width, int(round(width * min(current, target) / target)))
    return "█" * filled + "░" * (width - filled)


def escape(text: str) -> str:
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


async def safe_edit(
    message: Message,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    parse_mode: str | None = "HTML",
    **kwargs: Any,
) -> None:
    try:
        await message.edit_text(
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
            **kwargs,
        )
    except TelegramBadRequest as exc:
        err = str(exc).lower()
        if "message is not modified" in err:
            return
        if "there is no text in the message to edit" in err:
            try:
                await message.edit_caption(
                    caption=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode,
                )
                return
            except TelegramBadRequest:
                pass
        logger.warning("Не удалось отредактировать сообщение: %s", exc)
        try:
            await message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
        except TelegramBadRequest:
            logger.warning("Не удалось отправить запасное сообщение")
