# Habit Tracker Bot

Многопользовательский Telegram-бот для трекера привычек.

Каждый пользователь работает только со своими привычками, отметками, статистикой, напоминаниями и настройками. Идентификатор — Telegram user ID.

Стек:

- Python 3.12+
- aiogram 3.x
- SQLAlchemy 2.x
- SQLite по умолчанию (можно сменить на PostgreSQL через `DATABASE_URL`)
- APScheduler — напоминания
- zoneinfo — часовые пояса

## Возможности

- Регистрация при `/start` без отдельной формы
- Главное меню на inline-кнопках
- Создание, редактирование, удаление привычек (FSM)
- Бинарные и количественные цели
- Серии с учётом расписания (пропуск незапланированного дня не ломает серию)
- Статистика за 7 / 30 / 90 дней
- Календарь месяца
- Напоминания в часовом поясе пользователя
- Профиль и настройки
- Удаление всех своих данных
- Админ-панель (агрегированная статистика, без доступа к чужим привычкам)
- Отдельный раздел «Lolzteam привычка»: общие шаблоны, личные отметки, свои привычки, отдельная статистика и серии

## Установка (Windows)

1. Установите [Python 3.12+](https://www.python.org/downloads/). При установке отметьте **Add Python to PATH**.

2. Откройте PowerShell в папке проекта и создайте виртуальное окружение:

```powershell
python -m venv .venv
```

3. Активируйте окружение:

```powershell
.venv\Scripts\Activate.ps1
```

Если политика выполнения скриптов мешает активации:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

4. Установите зависимости:

```powershell
pip install -r requirements.txt
```

5. Создайте файл `.env` рядом с `bot.py` (можно скопировать `.env.example`):

```env
BOT_TOKEN=YOUR_BOT_TOKEN
ADMIN_ID=123456789
DATABASE_URL=sqlite+aiosqlite:///./data/habit_tracker.db
DEFAULT_TIMEZONE=Europe/Moscow
LOG_LEVEL=INFO
```

Токен берётся у [@BotFather](https://t.me/BotFather). `ADMIN_ID` — ваш Telegram user ID (например, через [@userinfobot](https://t.me/userinfobot)).

6. Запуск:

```powershell
python bot.py
```

## Установка (Linux / VPS)

```bash
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev
cd /opt
# распакуйте проект в /opt/habit_tracker_bot
cd /opt/habit_tracker_bot
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
python bot.py
```

Фоновый запуск через systemd (пример юнита):

```ini
[Unit]
Description=Habit Tracker Telegram Bot
After=network.target

[Service]
WorkingDirectory=/opt/habit_tracker_bot
ExecStart=/opt/habit_tracker_bot/.venv/bin/python bot.py
Restart=always
RestartSec=5
User=www-data

[Install]
WantedBy=multi-user.target
```

Перезапуск:

```bash
sudo systemctl restart habit-tracker
```

Остановка: `Ctrl+C` в консоли или `systemctl stop`.

## База данных

По умолчанию SQLite-файл создаётся автоматически:

```
./data/habit_tracker.db
```

Папка `data/` появится при первом запуске.

### Смена на PostgreSQL

В `.env`:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/habits
```

Дополнительно установите драйвер:

```bash
pip install asyncpg
```

Модели и запросы написаны через SQLAlchemy 2, без sqlite-специфики в бизнес-логике.

### Резервная копия SQLite

Остановите бота и скопируйте файл:

```bash
cp data/habit_tracker.db data/habit_tracker.db.bak
```

Или архив:

```bash
tar -czf habit_backup_$(date +%F).tar.gz data/habit_tracker.db
```

### Восстановление

Остановите бота, замените файл и запустите снова:

```bash
cp data/habit_tracker.db.bak data/habit_tracker.db
python bot.py
```

## Раздел Lolzteam

Отдельный трекер социальной активности на форуме. Бот **не** публикует сообщения, не ставит реакции и не заходит на форум — только хранит твои ручные отметки.

Готовые шаблоны лежат в таблице `lolzteam_habit_templates` и сидируются при запуске. Новые шаблоны админ добавляет из админки, без правки handlers.

Выполнения пользователей изолированы. Серии раздела не смешиваются с обычными привычками.

## Команды бота

| Команда     | Действие                          |
|-------------|-----------------------------------|
| `/start`    | Регистрация и главное меню        |
| `/help`     | Справка                           |
| `/cancel`   | Отмена текущего действия / FSM    |
| `/habits`   | Мои привычки                      |
| `/stats`    | Статистика                        |
| `/profile`  | Профиль                           |
| `/settings` | Настройки                         |

Основная работа идёт через кнопки.

## Безопасность

- `BOT_TOKEN` и `ADMIN_ID` только в `.env`
- Токен не пишется в логи
- Каждая привычка и отметка проверяются по `user_id` текущего Telegram-аккаунта
- ID в `callback_data` сами по себе правами не считаются
- Пользователь не может прочитать или изменить чужие привычки, подставив чужой ID

## Структура проекта

```
habit_tracker_bot/
├── bot.py
├── config.py
├── requirements.txt
├── .env.example
├── README.md
├── database/
├── handlers/
├── keyboards/
├── middlewares/
├── services/
├── states/
└── utils/
```

## Напоминания

Раз в минуту планировщик выбирает активные привычки с включённым напоминанием. Сообщение уходит только если:

- сейчас минута `reminder_time` в часовом поясе пользователя;
- привычка запланирована на этот день;
- привычка ещё не выполнена;
- уведомления в настройках включены;
- напоминание за этот день ещё не отправлялось.

## Лицензия

Проект можно использовать и изменять свободно для своих задач.
