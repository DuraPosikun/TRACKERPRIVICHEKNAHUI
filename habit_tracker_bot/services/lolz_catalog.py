from __future__ import annotations

# Категории раздела. Код хранится в БД, подпись показывается пользователю.
CATEGORIES: dict[str, str] = {
    "chat": "💬 Общение",
    "fun": "🎁 Развлечения",
    "content": "📝 Создание контента",
    "read": "📖 Просмотр/чтение",
    "react": "❤️ Взаимодействие",
    "custom": "➕ Свои",
}

# recommended_frequency: daily | few | weekly
# few = несколько раз в неделю (пн/ср/пт), weekly = раз в неделю (пн)
FREQ_PRESETS = {
    "daily": "daily",
    "few": "0,2,4",
    "weekly": "0",
}

FREQ_LABELS = {
    "daily": "каждый день",
    "few": "несколько раз в неделю",
    "weekly": "раз в неделю",
}


def preset_from_frequency(frequency: str) -> str:
    if frequency == "daily" or frequency == "0,1,2,3,4,5,6":
        return "daily"
    if frequency == "0,2,4":
        return "few"
    if frequency == "0":
        return "weekly"
    return "daily"


# Шаблоны собраны по публичным разделам форума:
# оффтоп (Offtopic), розыгрыши/халява (Giveaways/Freebies),
# темы и ответы, реакции (симпатии). Без автоматизации форума.
DEFAULT_TEMPLATES: list[dict] = [
    {
        "code": "offtopic_post",
        "title": "Написать бредик в оффтопе",
        "emoji": "💬",
        "category": "chat",
        "recommended_frequency": "daily",
        "sort_order": 10,
        "description": "Зайти в раздел Offtopic и написать короткий пост или комментарий. Бот ничего не публикует за тебя.",
    },
    {
        "code": "reply_thread",
        "title": "Ответить в интересной теме",
        "emoji": "💬",
        "category": "chat",
        "recommended_frequency": "daily",
        "sort_order": 20,
        "description": "Найти тему и оставить осмысленный ответ вручную.",
    },
    {
        "code": "chat_members",
        "title": "Пообщаться с участниками",
        "emoji": "👋",
        "category": "chat",
        "recommended_frequency": "daily",
        "sort_order": 30,
        "description": "Короткий диалог в теме или в переписке — без спама.",
    },
    {
        "code": "funny_comment",
        "title": "Оставить смешной комментарий",
        "emoji": "💭",
        "category": "chat",
        "recommended_frequency": "few",
        "sort_order": 40,
        "description": "Один живой комментарий в подходящей теме, не массовая рассылка.",
    },
    {
        "code": "create_giveaway",
        "title": "Создать розыгрыш",
        "emoji": "🎁",
        "category": "fun",
        "recommended_frequency": "weekly",
        "sort_order": 50,
        "description": "Раздел Giveaways / Розыгрыши. Создаёшь тему сам, бот только отмечает привычку.",
    },
    {
        "code": "join_giveaway",
        "title": "Поучаствовать в розыгрыше",
        "emoji": "🎫",
        "category": "fun",
        "recommended_frequency": "few",
        "sort_order": 60,
        "description": "Зайти в раздел розыгрышей и принять участие вручную.",
    },
    {
        "code": "new_thread",
        "title": "Создать новый пост",
        "emoji": "📝",
        "category": "content",
        "recommended_frequency": "weekly",
        "sort_order": 70,
        "description": "Новая тема в подходящем разделе форума.",
    },
    {
        "code": "read_threads",
        "title": "Прочитать несколько тем",
        "emoji": "📖",
        "category": "read",
        "recommended_frequency": "daily",
        "sort_order": 80,
        "description": "Прочитать 2–3 темы, которые реально интересны.",
    },
    {
        "code": "find_thread",
        "title": "Найти интересную тему",
        "emoji": "🔎",
        "category": "read",
        "recommended_frequency": "daily",
        "sort_order": 90,
        "description": "Пройтись по свежим темам и выбрать одну, которую стоит дочитать.",
    },
    {
        "code": "put_reactions",
        "title": "Поставить несколько реакций",
        "emoji": "❤️",
        "category": "react",
        "recommended_frequency": "daily",
        "sort_order": 100,
        "description": "Симпатии и реакции на форуме. Только вручную, без накрутки.",
    },
    {
        "code": "bookmark_thread",
        "title": "Отметить интересную тему",
        "emoji": "⭐",
        "category": "react",
        "recommended_frequency": "few",
        "sort_order": 110,
        "description": "Сохранить или отметить тему, к которой захочется вернуться.",
    },
]
