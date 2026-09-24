from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Habit, User
from handlers.common import is_admin
from keyboards.habits import (
    add_confirm_kb,
    add_description_kb,
    add_frequency_kb,
    add_reminder_kb,
    custom_days_kb,
    delete_habit_kb,
    habit_actions_kb,
    habit_edit_fields_kb,
    habits_list_kb,
    skip_value_kb,
)
from keyboards.main import main_menu_kb
from services.habit_service import HabitService
from services.streak_service import StreakService
from states.habits import AddHabit, EditHabit
from utils.dates import format_date, frequency_label, format_time, is_scheduled_on, local_today
from utils.formatters import escape, progress_bar, safe_edit

router = Router(name="habits")

NAME_MIN, NAME_MAX = 1, 64
DESC_MAX = 500
TARGET_MAX = 1000


def _tz(user: User) -> str:
    return user.settings.timezone if user.settings else "Europe/Moscow"


def _tf(user: User) -> str:
    return user.settings.time_format if user.settings else "24"


async def render_habits(
    target: Message,
    session: AsyncSession,
    user: User,
    *,
    edit: bool,
) -> None:
    service = HabitService(session)
    today = local_today(_tz(user))
    habits = await service.list_active(user.id)
    planned = [h for h in habits if is_scheduled_on(h.frequency, today)]
    completions = await service.completions_for_user_on(user.id, today)
    marks: dict[int, bool] = {}
    lines = [f"<b>Сегодня, {format_date(today)}</b>\n"]
    if not planned:
        if habits:
            lines.append("На сегодня нет запланированных привычек.")
        else:
            lines.append("Пока нет привычек. Нажми «Добавить».")
    for habit in planned:
        comp = completions.get(habit.id)
        done = StreakService.is_done(habit, comp)
        marks[habit.id] = done
        check = "☑️" if done else "⬜"
        value = comp.value if comp else 0
        if habit.target > 1:
            bar = progress_bar(value, habit.target)
            lines.append(f"{check} {habit.emoji} {escape(habit.name)}\n{bar} {value}/{habit.target}")
        else:
            lines.append(f"{check} {habit.emoji} {escape(habit.name)}")
    text = "\n".join(lines)
    markup = habits_list_kb(planned or habits, marks)
    if edit:
        await safe_edit(target, text, reply_markup=markup)
    else:
        await target.answer(text, reply_markup=markup, parse_mode="HTML")


@router.message(Command("habits"))
@router.callback_query(F.data == "menu:habits")
async def show_habits(
    event: Message | CallbackQuery,
    session: AsyncSession,
    db_user: User,
) -> None:
    if isinstance(event, CallbackQuery):
        await event.answer()
        await render_habits(event.message, session, db_user, edit=True)
    else:
        await render_habits(event, session, db_user, edit=False)


@router.callback_query(F.data == "menu:add")
async def start_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AddHabit.name)
    await callback.answer()
    await safe_edit(
        callback.message,
        "Как назвать привычку?\n\nНапример: <i>Выпить воду</i>\n\n/cancel — отмена",
        reply_markup=skip_value_kb(),
    )


@router.message(StateFilter(AddHabit.name))
async def add_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name or name.startswith("/"):
        await message.answer("Введите название текстом, без команды.")
        return
    if not (NAME_MIN <= len(name) <= NAME_MAX):
        await message.answer(f"Название должно быть от {NAME_MIN} до {NAME_MAX} символов.")
        return
    await state.update_data(name=name)
    await state.set_state(AddHabit.emoji)
    await message.answer(
        "Выберите эмодзи для привычки.\nОтправьте один символ, например 💧",
        reply_markup=skip_value_kb(),
    )


@router.message(StateFilter(AddHabit.emoji))
async def add_emoji(message: Message, state: FSMContext) -> None:
    emoji = (message.text or "").strip()
    if not emoji or emoji.startswith("/"):
        await message.answer("Отправьте эмодзи сообщением.")
        return
    if len(emoji) > 16:
        await message.answer("Слишком длинно. Достаточно одного эмодзи.")
        return
    await state.update_data(emoji=emoji)
    await state.set_state(AddHabit.description)
    await message.answer(
        "Описание (необязательно). Можно пропустить.",
        reply_markup=add_description_kb(),
    )


@router.callback_query(StateFilter(AddHabit.description), F.data == "add:skip_desc")
async def add_skip_desc(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(description=None)
    await state.set_state(AddHabit.frequency)
    await callback.answer()
    await safe_edit(
        callback.message,
        "Как часто выполнять привычку?",
        reply_markup=add_frequency_kb(),
    )


@router.message(StateFilter(AddHabit.description))
async def add_desc(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text in {"-", "нет", "skip"}:
        text = ""
    if len(text) > DESC_MAX:
        await message.answer(f"Описание слишком длинное (макс. {DESC_MAX}).")
        return
    await state.update_data(description=text or None)
    await state.set_state(AddHabit.frequency)
    await message.answer("Как часто выполнять привычку?", reply_markup=add_frequency_kb())


@router.callback_query(StateFilter(AddHabit.frequency), F.data.startswith("add:freq:"))
async def add_freq(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.split(":")[-1]
    await callback.answer()
    if value == "custom":
        await state.update_data(custom_days=[])
        await state.set_state(AddHabit.custom_days)
        await safe_edit(
            callback.message,
            "Отметьте нужные дни недели, затем «Готово».",
            reply_markup=custom_days_kb(set()),
        )
        return
    if value == "daily":
        frequency = "daily"
    else:
        frequency = value
    await state.update_data(frequency=frequency)
    await state.set_state(AddHabit.target)
    await safe_edit(
        callback.message,
        "Какая цель за день?\n\n"
        "1 — просто выполнить / не выполнить.\n"
        "Число больше 1 — количественная цель (например 8 стаканов воды).",
        reply_markup=skip_value_kb(),
    )


@router.callback_query(StateFilter(AddHabit.custom_days), F.data.startswith("add:day:"))
async def add_custom_day(callback: CallbackQuery, state: FSMContext) -> None:
    token = callback.data.split(":")[-1]
    data = await state.get_data()
    selected = set(int(x) for x in data.get("custom_days", []))
    if token == "done":
        if not selected:
            await callback.answer("Выберите хотя бы один день", show_alert=True)
            return
        frequency = ",".join(str(i) for i in sorted(selected))
        await state.update_data(frequency=frequency)
        await state.set_state(AddHabit.target)
        await callback.answer()
        await safe_edit(
            callback.message,
            "Какая цель за день? 1 — бинарная, больше 1 — количество.",
            reply_markup=skip_value_kb(),
        )
        return
    if not token.isdigit():
        await callback.answer()
        return
    day = int(token)
    if day in selected:
        selected.remove(day)
    else:
        selected.add(day)
    await state.update_data(custom_days=sorted(selected))
    await callback.answer()
    await safe_edit(
        callback.message,
        "Отметьте нужные дни недели, затем «Готово».",
        reply_markup=custom_days_kb(selected),
    )


@router.message(StateFilter(AddHabit.target))
async def add_target(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("Введите целое число от 1 до 1000.")
        return
    target = int(raw)
    if not (1 <= target <= TARGET_MAX):
        await message.answer("Цель должна быть от 1 до 1000.")
        return
    await state.update_data(target=target)
    await state.set_state(AddHabit.reminder)
    await message.answer("Нужно ли напоминание?", reply_markup=add_reminder_kb())


@router.callback_query(StateFilter(AddHabit.reminder), F.data.startswith("add:rem:"))
async def add_reminder(callback: CallbackQuery, state: FSMContext) -> None:
    enabled = callback.data.endswith(":1")
    await state.update_data(reminder_enabled=enabled)
    await callback.answer()
    if enabled:
        await state.set_state(AddHabit.reminder_time)
        await safe_edit(
            callback.message,
            "Введите время напоминания, например <b>19:00</b>",
            reply_markup=skip_value_kb(),
        )
        return
    await state.update_data(reminder_time=None)
    await state.set_state(AddHabit.confirm)
    await _show_confirm(callback.message, state, edit=True)


@router.message(StateFilter(AddHabit.reminder_time))
async def add_reminder_time(message: Message, state: FSMContext) -> None:
    from utils.dates import parse_time

    parsed = parse_time(message.text or "")
    if parsed is None:
        await message.answer("Не понял время. Пример: 07:30 или 19:00")
        return
    await state.update_data(reminder_time=parsed.isoformat())
    await state.set_state(AddHabit.confirm)
    await _show_confirm(message, state, edit=False)


async def _show_confirm(target: Message, state: FSMContext, *, edit: bool) -> None:
    data = await state.get_data()
    rem = "да" if data.get("reminder_enabled") else "нет"
    rtime = data.get("reminder_time") or "—"
    desc = data.get("description") or "—"
    text = (
        "<b>Проверьте привычку</b>\n\n"
        f"{data.get('emoji', '✅')} <b>{escape(str(data.get('name', '')))}</b>\n"
        f"Описание: {escape(str(desc))}\n"
        f"Периодичность: {frequency_label(str(data.get('frequency', 'daily')))}\n"
        f"Цель: {data.get('target', 1)}\n"
        f"Напоминание: {rem}\n"
        f"Время: {rtime}"
    )
    if edit:
        await safe_edit(target, text, reply_markup=add_confirm_kb())
    else:
        await target.answer(text, parse_mode="HTML", reply_markup=add_confirm_kb())


@router.callback_query(StateFilter(AddHabit.confirm), F.data == "add:ok")
async def add_ok(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    db_user: User,
) -> None:
    from datetime import time as time_cls

    data = await state.get_data()
    rtime_raw = data.get("reminder_time")
    rtime = time_cls.fromisoformat(rtime_raw) if rtime_raw else None
    service = HabitService(session)
    habit = await service.create(
        db_user,
        name=str(data.get("name", "Привычка")),
        emoji=str(data.get("emoji", "✅")),
        description=data.get("description"),
        frequency=str(data.get("frequency", "daily")),
        target=int(data.get("target") or 1),
        reminder_enabled=bool(data.get("reminder_enabled")),
        reminder_time=rtime,
    )
    await state.clear()
    await callback.answer("Создано")
    await safe_edit(
        callback.message,
        f"Привычка {habit.emoji} <b>{escape(habit.name)}</b> создана.",
        reply_markup=main_menu_kb(is_admin=is_admin(callback.from_user.id)),
    )


async def _habit_card_text(
    habit: Habit,
    session: AsyncSession,
    user: User,
) -> tuple[str, int, bool]:
    today = local_today(_tz(user))
    service = HabitService(session)
    comp = await service.get_completion(habit.id, user.id, today)
    value = comp.value if comp else 0
    done = StreakService.is_done(habit, comp)
    completions = await service.habit_completions_in_range(
        habit.id, user.id, habit.created_at.date(), today
    )
    stats = StreakService.stats(habit, completions, today)
    rem = "выкл"
    if habit.reminder_enabled and habit.reminder_time:
        rem = format_time(habit.reminder_time, _tf(user))
    desc = habit.description or "—"
    bar = ""
    if habit.target > 1:
        bar = f"\n{progress_bar(value, habit.target)} {value}/{habit.target}"
    status = "☑️ Выполнено" if done else "⬜ Не выполнено"
    text = (
        f"{habit.emoji} <b>{escape(habit.name)}</b>\n\n"
        f"{status}{bar}\n\n"
        f"{escape(desc)}\n\n"
        f"📅 {frequency_label(habit.frequency)}\n"
        f"🎯 Цель: {habit.target}\n"
        f"⏰ Напоминание: {rem}\n\n"
        f"🔥 Текущая серия: {stats.current_streak} дн.\n"
        f"🏆 Лучшая серия: {stats.best_streak} дн.\n"
        f"✅ Выполнено: {stats.completions_count} раз\n"
        f"📈 Выполнение: {stats.percent:.0f}%"
    )
    return text, value, done


@router.callback_query(F.data.startswith("h:v:"))
async def view_habit(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
) -> None:
    habit_id = _parse_id(callback.data)
    if habit_id is None:
        await callback.answer("Некорректные данные", show_alert=True)
        return
    service = HabitService(session)
    habit = await service.get_owned(habit_id, db_user.id)
    if habit is None:
        await callback.answer("Привычка не найдена", show_alert=True)
        return
    text, value, done = await _habit_card_text(habit, session, db_user)
    await callback.answer()
    await safe_edit(callback.message, text, reply_markup=habit_actions_kb(habit, done=done, value=value))


@router.callback_query(F.data.startswith("h:tg:"))
async def toggle_habit(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
) -> None:
    habit_id = _parse_id(callback.data)
    service = HabitService(session)
    habit = await service.get_owned(habit_id or -1, db_user.id)
    if habit is None:
        await callback.answer("Привычка не найдена", show_alert=True)
        return
    today = local_today(_tz(db_user))
    result = await service.toggle_binary(habit, today)
    await callback.answer("Отмечено" if result else "Снято")
    text, value, done = await _habit_card_text(habit, session, db_user)
    await safe_edit(callback.message, text, reply_markup=habit_actions_kb(habit, done=done, value=value))


@router.callback_query(F.data.startswith("h:inc:") | F.data.startswith("h:dec:"))
async def change_value(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
) -> None:
    habit_id = _parse_id(callback.data)
    service = HabitService(session)
    habit = await service.get_owned(habit_id or -1, db_user.id)
    if habit is None:
        await callback.answer("Привычка не найдена", show_alert=True)
        return
    today = local_today(_tz(db_user))
    delta = 1 if callback.data.startswith("h:inc:") else -1
    await service.increment(habit, today, delta)
    await callback.answer()
    text, value, done = await _habit_card_text(habit, session, db_user)
    await safe_edit(callback.message, text, reply_markup=habit_actions_kb(habit, done=done, value=value))


@router.callback_query(F.data.startswith("h:dl:"))
async def ask_delete(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
) -> None:
    habit_id = _parse_id(callback.data)
    service = HabitService(session)
    habit = await service.get_owned(habit_id or -1, db_user.id)
    if habit is None:
        await callback.answer("Привычка не найдена", show_alert=True)
        return
    await callback.answer()
    await safe_edit(
        callback.message,
        f"Удалить привычку {habit.emoji} <b>{escape(habit.name)}</b>?",
        reply_markup=delete_habit_kb(habit.id),
    )


@router.callback_query(F.data.startswith("h:dx:"))
async def do_delete(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
) -> None:
    habit_id = _parse_id(callback.data)
    service = HabitService(session)
    habit = await service.get_owned(habit_id or -1, db_user.id)
    if habit is None:
        await callback.answer("Привычка не найдена", show_alert=True)
        return
    name = f"{habit.emoji} {habit.name}"
    await service.delete_owned(habit)
    await callback.answer("Удалено")
    await safe_edit(
        callback.message,
        f"Привычка {escape(name)} удалена.",
        reply_markup=main_menu_kb(is_admin=is_admin(callback.from_user.id)),
    )


@router.callback_query(F.data.startswith("h:ed:"))
async def edit_menu(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
    state: FSMContext,
) -> None:
    await state.clear()
    habit_id = _parse_id(callback.data)
    service = HabitService(session)
    habit = await service.get_owned(habit_id or -1, db_user.id)
    if habit is None:
        await callback.answer("Привычка не найдена", show_alert=True)
        return
    await callback.answer()
    await safe_edit(
        callback.message,
        f"Что изменить у {habit.emoji} <b>{escape(habit.name)}</b>?",
        reply_markup=habit_edit_fields_kb(habit.id),
    )


@router.callback_query(F.data.startswith("h:ef:"))
async def edit_field(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
    state: FSMContext,
) -> None:
    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer("Некорректные данные", show_alert=True)
        return
    habit_id = int(parts[2]) if parts[2].isdigit() else -1
    field = parts[3]
    service = HabitService(session)
    habit = await service.get_owned(habit_id, db_user.id)
    if habit is None:
        await callback.answer("Привычка не найдена", show_alert=True)
        return
    await callback.answer()
    if field == "freq":
        await state.update_data(edit_habit_id=habit.id, edit_field="freq", custom_days=[])
        await state.set_state(EditHabit.custom_days)
        await safe_edit(
            callback.message,
            "Выберите периодичность.",
            reply_markup=add_frequency_kb(),
        )
        return
    if field == "rem":
        new_val = not habit.reminder_enabled
        await service.update(habit, reminder_enabled=new_val)
        if new_val and habit.reminder_time is None:
            await state.update_data(edit_habit_id=habit.id, edit_field="rtime")
            await state.set_state(EditHabit.reminder_time)
            await safe_edit(
                callback.message,
                "Напоминания включены. Введите время, например 19:00",
                reply_markup=skip_value_kb(),
            )
            return
        text, value, done = await _habit_card_text(habit, session, db_user)
        await safe_edit(callback.message, text, reply_markup=habit_actions_kb(habit, done=done, value=value))
        return
    prompts = {
        "name": "Введите новое название.",
        "emoji": "Отправьте новый эмодзи.",
        "desc": "Введите новое описание или «-», чтобы очистить.",
        "target": "Введите новую цель (число от 1 до 1000).",
        "rtime": "Введите время напоминания, например 19:00",
    }
    if field not in prompts:
        await callback.answer("Неизвестное поле", show_alert=True)
        return
    await state.update_data(edit_habit_id=habit.id, edit_field=field)
    if field == "rtime":
        await state.set_state(EditHabit.reminder_time)
    else:
        await state.set_state(EditHabit.waiting_value)
    await safe_edit(callback.message, prompts[field], reply_markup=skip_value_kb())


@router.callback_query(StateFilter(EditHabit.custom_days), F.data.startswith("add:freq:"))
async def edit_freq_choice(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    db_user: User,
) -> None:
    value = callback.data.split(":")[-1]
    data = await state.get_data()
    habit_id = int(data.get("edit_habit_id") or 0)
    service = HabitService(session)
    habit = await service.get_owned(habit_id, db_user.id)
    if habit is None:
        await state.clear()
        await callback.answer("Привычка не найдена", show_alert=True)
        return
    await callback.answer()
    if value == "custom":
        await state.update_data(custom_days=[])
        await safe_edit(
            callback.message,
            "Отметьте дни, затем «Готово».",
            reply_markup=custom_days_kb(set()),
        )
        return
    frequency = "daily" if value == "daily" else value
    await service.update(habit, frequency=frequency)
    await state.clear()
    text, val, done = await _habit_card_text(habit, session, db_user)
    await safe_edit(callback.message, text, reply_markup=habit_actions_kb(habit, done=done, value=val))


@router.callback_query(StateFilter(EditHabit.custom_days), F.data.startswith("add:day:"))
async def edit_custom_days(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    db_user: User,
) -> None:
    token = callback.data.split(":")[-1]
    data = await state.get_data()
    selected = set(int(x) for x in data.get("custom_days", []))
    habit_id = int(data.get("edit_habit_id") or 0)
    if token == "done":
        if not selected:
            await callback.answer("Выберите хотя бы один день", show_alert=True)
            return
        service = HabitService(session)
        habit = await service.get_owned(habit_id, db_user.id)
        if habit is None:
            await state.clear()
            await callback.answer("Привычка не найдена", show_alert=True)
            return
        await service.update(habit, frequency=",".join(str(i) for i in sorted(selected)))
        await state.clear()
        await callback.answer("Сохранено")
        text, val, done = await _habit_card_text(habit, session, db_user)
        await safe_edit(callback.message, text, reply_markup=habit_actions_kb(habit, done=done, value=val))
        return
    if token.isdigit():
        day = int(token)
        if day in selected:
            selected.remove(day)
        else:
            selected.add(day)
        await state.update_data(custom_days=sorted(selected))
        await callback.answer()
        await safe_edit(
            callback.message,
            "Отметьте дни, затем «Готово».",
            reply_markup=custom_days_kb(selected),
        )


@router.message(StateFilter(EditHabit.waiting_value, EditHabit.reminder_time))
async def edit_value(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: User,
) -> None:
    from datetime import time as time_cls

    from utils.dates import parse_time

    data = await state.get_data()
    habit_id = int(data.get("edit_habit_id") or 0)
    field = data.get("edit_field")
    service = HabitService(session)
    habit = await service.get_owned(habit_id, db_user.id)
    if habit is None:
        await state.clear()
        await message.answer("Привычка не найдена.", reply_markup=main_menu_kb(is_admin=is_admin(message.from_user.id)))
        return
    raw = (message.text or "").strip()
    try:
        if field == "name":
            if not (NAME_MIN <= len(raw) <= NAME_MAX):
                await message.answer(f"Название: {NAME_MIN}–{NAME_MAX} символов.")
                return
            await service.update(habit, name=raw)
        elif field == "emoji":
            if not raw or len(raw) > 16:
                await message.answer("Отправьте один эмодзи.")
                return
            await service.update(habit, emoji=raw)
        elif field == "desc":
            if raw in {"-", "нет"}:
                raw = ""
            if len(raw) > DESC_MAX:
                await message.answer(f"Максимум {DESC_MAX} символов.")
                return
            await service.update(habit, description=raw or None)
        elif field == "target":
            if not raw.isdigit() or not (1 <= int(raw) <= TARGET_MAX):
                await message.answer("Число от 1 до 1000.")
                return
            await service.update(habit, target=int(raw))
        elif field == "rtime":
            parsed = parse_time(raw)
            if parsed is None:
                await message.answer("Пример времени: 19:00")
                return
            await service.update(habit, reminder_time=parsed, reminder_enabled=True)
        else:
            await message.answer("Неизвестное поле.")
            await state.clear()
            return
    except Exception:
        await message.answer("Не получилось сохранить. Попробуйте ещё раз.")
        return
    await state.clear()
    text, val, done = await _habit_card_text(habit, session, db_user)
    await message.answer(text, parse_mode="HTML", reply_markup=habit_actions_kb(habit, done=done, value=val))


def _parse_id(data: str | None) -> int | None:
    if not data:
        return None
    parts = data.split(":")
    if len(parts) < 3 or not parts[2].isdigit():
        return None
    return int(parts[2])
