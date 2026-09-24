from __future__ import annotations

from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

WEEKDAY_NAMES = [
    "понедельник",
    "вторник",
    "среда",
    "четверг",
    "пятница",
    "суббота",
    "воскресенье",
]
WEEKDAY_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
MONTH_NAMES = [
    "",
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
]
MONTH_TITLES = [
    "",
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
]


def get_zone(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("Europe/Moscow")


def local_now(tz_name: str) -> datetime:
    return datetime.now(get_zone(tz_name))


def local_today(tz_name: str) -> date:
    return local_now(tz_name).date()


def weekday_index(d: date) -> int:
    """Monday = 0 ... Sunday = 6."""
    return d.weekday()


def format_date(d: date) -> str:
    return f"{d.day} {MONTH_NAMES[d.month]} {d.year}"


def format_date_short(d: date) -> str:
    return d.strftime("%d.%m.%Y")


def format_time(t: time, time_format: str = "24") -> str:
    if time_format == "12":
        return t.strftime("%I:%M %p").lstrip("0")
    return t.strftime("%H:%M")


def parse_time(raw: str) -> time | None:
    text = (raw or "").strip().lower().replace(".", ":").replace("-", ":")
    text = text.replace(" ", "")
    ampm = None
    if text.endswith("am") or text.endswith("pm"):
        ampm = text[-2:]
        text = text[:-2]
    parts = text.split(":")
    if len(parts) not in (1, 2):
        return None
    try:
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) == 2 else 0
    except ValueError:
        return None
    if ampm == "pm" and hour < 12:
        hour += 12
    if ampm == "am" and hour == 12:
        hour = 0
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return time(hour, minute)


def is_scheduled_on(frequency: str, d: date) -> bool:
    if frequency == "daily" or frequency == "0,1,2,3,4,5,6":
        return True
    days = set()
    for part in frequency.split(","):
        part = part.strip()
        if part.isdigit():
            days.add(int(part))
    return weekday_index(d) in days


def frequency_label(frequency: str) -> str:
    if frequency == "daily" or frequency == "0,1,2,3,4,5,6":
        return "каждый день"
    days = []
    for part in frequency.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part)
            if 0 <= idx <= 6:
                days.append(WEEKDAY_NAMES[idx])
    if not days:
        return "не задано"
    return ", ".join(days)


def scheduled_dates_between(frequency: str, start: date, end: date) -> list[date]:
    result: list[date] = []
    current = start
    delta_days = (end - start).days
    from datetime import timedelta

    for i in range(delta_days + 1):
        day = start + timedelta(days=i)
        if is_scheduled_on(frequency, day):
            result.append(day)
        current = day
    return result
