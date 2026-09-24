from __future__ import annotations

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

TIMEZONES: list[tuple[str, str, str]] = [
    ("Pacific/Honolulu", "Гонолулу", "UTC-10"),
    ("America/Anchorage", "Анкоридж", "UTC-9"),
    ("America/Los_Angeles", "Лос-Анджелес", "UTC-8"),
    ("America/Denver", "Денвер", "UTC-7"),
    ("America/Chicago", "Чикаго", "UTC-6"),
    ("America/New_York", "Нью-Йорк", "UTC-5"),
    ("America/Sao_Paulo", "Сан-Паулу", "UTC-3"),
    ("Atlantic/Azores", "Азорские о-ва", "UTC-1"),
    ("UTC", "UTC", "UTC+0"),
    ("Europe/London", "Лондон", "UTC+0"),
    ("Europe/Lisbon", "Лиссабон", "UTC+0"),
    ("Europe/Paris", "Париж", "UTC+1"),
    ("Europe/Berlin", "Берлин", "UTC+1"),
    ("Europe/Rome", "Рим", "UTC+1"),
    ("Europe/Warsaw", "Варшава", "UTC+1"),
    ("Europe/Prague", "Прага", "UTC+1"),
    ("Europe/Amsterdam", "Амстердам", "UTC+1"),
    ("Europe/Kaliningrad", "Калининград", "UTC+2"),
    ("Europe/Kiev", "Киев", "UTC+2"),
    ("Europe/Helsinki", "Хельсинки", "UTC+2"),
    ("Europe/Athens", "Афины", "UTC+2"),
    ("Europe/Bucharest", "Бухарест", "UTC+2"),
    ("Africa/Cairo", "Каир", "UTC+2"),
    ("Europe/Moscow", "Москва", "UTC+3"),
    ("Europe/Minsk", "Минск", "UTC+3"),
    ("Europe/Istanbul", "Стамбул", "UTC+3"),
    ("Asia/Riyadh", "Эр-Рияд", "UTC+3"),
    ("Europe/Samara", "Самара", "UTC+4"),
    ("Asia/Dubai", "Дубай", "UTC+4"),
    ("Asia/Tbilisi", "Тбилиси", "UTC+4"),
    ("Asia/Yekaterinburg", "Екатеринбург", "UTC+5"),
    ("Asia/Tashkent", "Ташкент", "UTC+5"),
    ("Asia/Almaty", "Алматы", "UTC+6"),
    ("Asia/Omsk", "Омск", "UTC+6"),
    ("Asia/Novosibirsk", "Новосибирск", "UTC+7"),
    ("Asia/Krasnoyarsk", "Красноярск", "UTC+7"),
    ("Asia/Bangkok", "Бангкок", "UTC+7"),
    ("Asia/Jakarta", "Джакарта", "UTC+7"),
    ("Asia/Irkutsk", "Иркутск", "UTC+8"),
    ("Asia/Singapore", "Сингапур", "UTC+8"),
    ("Asia/Shanghai", "Шанхай", "UTC+8"),
    ("Asia/Hong_Kong", "Гонконг", "UTC+8"),
    ("Asia/Yakutsk", "Якутск", "UTC+9"),
    ("Asia/Tokyo", "Токио", "UTC+9"),
    ("Asia/Seoul", "Сеул", "UTC+9"),
    ("Asia/Vladivostok", "Владивосток", "UTC+10"),
    ("Australia/Sydney", "Сидней", "UTC+10"),
    ("Asia/Magadan", "Магадан", "UTC+11"),
    ("Asia/Kamchatka", "Камчатка", "UTC+12"),
    ("Pacific/Auckland", "Окленд", "UTC+12"),
]


def timezone_label(tz_name: str) -> str:
    for name, city, offset in TIMEZONES:
        if name == tz_name:
            return f"{city} {offset}"
    return tz_name


def timezone_by_index(index: int) -> str | None:
    if 0 <= index < len(TIMEZONES):
        return TIMEZONES[index][0]
    return None


def valid_timezone(name: str) -> bool:
    try:
        ZoneInfo(name)
        return True
    except ZoneInfoNotFoundError:
        return False
