from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import LolzUserHabit, User
from keyboards.lolz import (
    lolz_add_kb,
    lolz_custom_cancel_kb,
    lolz_custom_freq_kb,
    lolz_freq_kb,
    lolz_habit_kb,
    lolz_home_kb,
    lolz_mine_kb,
    lolz_stats_kb,
    lolz_template_kb,
    lolz_templates_kb,
)
from keyboards.main import main_menu_kb
from handlers.common import is_admin
from services.lolz_catalog import CATEGORIES, FREQ_LABELS, FREQ_PRESETS, preset_from_frequency
from services.lolz_service import LolzService, lolz_overview
from states.lolz import AddLolzCustom
from utils.dates import format_date, frequency_label, is_scheduled_on, local_today
from utils.formatters import escape, safe_edit

router = Router(name="lolz")


def _tz(user: User) -> str:
    return user.settings.timezone if user.settings else "Europe/Moscow"


async def render_lolz_home(
    target: Message,
    session: AsyncSession,
    user: User,
    *,
    edit: bool,
) -> None:
    service = LolzService(session)
    await service.seed_templates()
    today = local_today(_tz(user))
    habits = await service.list_user_habits(user.id)
    planned = [h for h in habits if is_scheduled_on(h.frequency, today)]
    comps = await service.completions_on(user.id, today)
    marks = {h.id: h.id in comps for h in planned}

    start = min((h.created_at.date() for h in habits), default=today)
    all_comps = await service.completions_in_range(user.id, start, today) if habits else []
    overview = lolz_overview(habits, all_comps, today)

    lines = [
        "<b>🌐 LOLZTEAM ПРИВЫЧКА</b>",
        "",
        f"🔥 Твоя серия: {overview.current_streak} дн.",
        f"Сегодня, {format_date(today)}:",
        "",
    ]
    if not planned:
        if habits:
            lines.append("На сегодня нет запланированных привычек этого раздела.")
        else:
            lines.append("Список пуст. Добавь готовую или свою привычку.")
    for habit in planned:
        check = "☑️" if marks.get(habit.id) else "⬜"
        lines.append(f"{check} {habit.emoji} {escape(habit.title)}")
    lines.append("")
    lines.append("Отметки только ручные. Бот не пишет на форум.")
    text = "\n".join(lines)
    markup = lolz_home_kb(planned or habits, marks)
    if edit:
        await safe_edit(target, text, reply_markup=markup)
    else:
        await target.answer(text, parse_mode="HTML", reply_markup=markup)


@router.callback_query(F.data == "menu:lolz")
async def cb_lolz_home(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
    state: FSMContext,
) -> None:
    await state.clear()
    await callback.answer()
    await render_lolz_home(callback.message, session, db_user, edit=True)


@router.callback_query(F.data == "lz:st")
async def cb_lolz_stats(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
) -> None:
    service = LolzService(session)
    today = local_today(_tz(db_user))
    habits = await service.list_user_habits(db_user.id)
    start = min((h.created_at.date() for h in habits), default=today - __import__("datetime").timedelta(days=30))
    comps = await service.completions_in_range(db_user.id, start, today)
    overview = lolz_overview(habits, comps, today)
    top = overview.top_habit or "—"
    text = (
        "<b>🌐 LOLZTEAM СТАТИСТИКА</b>\n\n"
        f"Сегодня: {overview.today_done}/{overview.today_scheduled}\n"
        f"За неделю: {overview.week_done}\n"
        f"За месяц: {overview.month_done}\n\n"
        f"🔥 Текущая серия: {overview.current_streak} дн.\n"
        f"🏆 Лучшая серия: {overview.best_streak} дн.\n"
        f"✅ Всего отметок: {overview.total_done}\n"
        f"⭐ Чаще всего: {escape(top)}\n\n"
        "Серии этого раздела не смешиваются с обычными привычками."
    )
    await callback.answer()
    await safe_edit(callback.message, text, reply_markup=lolz_stats_kb())


@router.callback_query(F.data == "lz:add")
async def cb_lolz_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    await safe_edit(
        callback.message,
        "<b>Добавить Lolzteam-привычку</b>\n\nВыбери категорию или создай свою.",
        reply_markup=lolz_add_kb(),
    )


@router.callback_query(F.data.startswith("lz:cat:"))
async def cb_lolz_cat(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
) -> None:
    cat = callback.data.split(":")[-1]
    if cat not in CATEGORIES or cat == "custom":
        await callback.answer("Нет такой категории", show_alert=True)
        return
    service = LolzService(session)
    templates = [t for t in await service.list_templates() if t.category == cat]
    taken = {
        h.template_id
        for h in await service.list_user_habits(db_user.id)
        if h.template_id is not None
    }
    await callback.answer()
    await safe_edit(
        callback.message,
        f"<b>{CATEGORIES[cat]}</b>\n\nВыбери шаблон. Выполнение будет только у тебя.",
        reply_markup=lolz_templates_kb(templates, taken),
    )


@router.callback_query(F.data.startswith("lz:tpl:"))
async def cb_lolz_tpl(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
) -> None:
    raw = callback.data.split(":")[-1]
    if not raw.isdigit():
        await callback.answer()
        return
    service = LolzService(session)
    template = await service.get_template(int(raw))
    if template is None or not template.is_active:
        await callback.answer("Шаблон недоступен", show_alert=True)
        return
    mine = await service.list_user_habits(db_user.id)
    already = any(h.template_id == template.id for h in mine)
    freq = FREQ_LABELS.get(template.recommended_frequency, template.recommended_frequency)
    text = (
        f"{template.emoji} <b>{escape(template.title)}</b>\n\n"
        f"{escape(template.description or '—')}\n\n"
        f"Категория: {CATEGORIES.get(template.category, template.category)}\n"
        f"Рекомендуемая периодичность: {freq}"
    )
    await callback.answer()
    await safe_edit(callback.message, text, reply_markup=lolz_template_kb(template.id, already))


@router.callback_query(F.data.startswith("lz:on:"))
async def cb_lolz_on(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
) -> None:
    raw = callback.data.split(":")[-1]
    service = LolzService(session)
    template = await service.get_template(int(raw) if raw.isdigit() else -1)
    if template is None or not template.is_active:
        await callback.answer("Шаблон недоступен", show_alert=True)
        return
    await service.activate_template(db_user, template)
    await callback.answer("Добавлено")
    await render_lolz_home(callback.message, session, db_user, edit=True)


@router.callback_query(F.data.startswith("lz:v:"))
async def cb_lolz_view(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
) -> None:
    habit = await _owned(callback, session, db_user)
    if habit is None:
        return
    today = local_today(_tz(db_user))
    service = LolzService(session)
    done = await service.get_completion(habit.id, db_user.id, today) is not None
    preset = preset_from_frequency(habit.frequency)
    text = (
        f"{habit.emoji} <b>{escape(habit.title)}</b>\n\n"
        f"{escape(habit.description or '—')}\n\n"
        f"{'☑️ Выполнено сегодня' if done else '⬜ Сегодня не отмечено'}\n"
        f"📅 {frequency_label(habit.frequency)} ({FREQ_LABELS.get(preset, preset)})\n"
        f"📂 {CATEGORIES.get(habit.category, habit.category)}"
    )
    await callback.answer()
    await safe_edit(callback.message, text, reply_markup=lolz_habit_kb(habit, done=done))


@router.callback_query(F.data.startswith("lz:tg:"))
async def cb_lolz_toggle(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
) -> None:
    habit = await _owned(callback, session, db_user)
    if habit is None:
        return
    service = LolzService(session)
    today = local_today(_tz(db_user))
    result = await service.toggle(habit, today)
    await callback.answer("Отмечено" if result else "Снято")
    await render_lolz_home(callback.message, session, db_user, edit=True)


@router.callback_query(F.data.startswith("lz:fr:"))
async def cb_lolz_freq_menu(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
) -> None:
    habit = await _owned(callback, session, db_user)
    if habit is None:
        return
    await callback.answer()
    await safe_edit(
        callback.message,
        f"Периодичность для {habit.emoji} <b>{escape(habit.title)}</b>",
        reply_markup=lolz_freq_kb(habit.id),
    )


@router.callback_query(F.data.startswith("lz:fs:"))
async def cb_lolz_freq_set(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
) -> None:
    parts = callback.data.split(":")
    if len(parts) != 4 or not parts[2].isdigit():
        await callback.answer()
        return
    service = LolzService(session)
    habit = await service.get_owned(int(parts[2]), db_user.id)
    if habit is None:
        await callback.answer("Не найдено", show_alert=True)
        return
    await service.set_frequency(habit, parts[3])
    await callback.answer("Сохранено")
    today = local_today(_tz(db_user))
    done = await service.get_completion(habit.id, db_user.id, today) is not None
    await safe_edit(
        callback.message,
        f"{habit.emoji} <b>{escape(habit.title)}</b>\nПериодичность обновлена.",
        reply_markup=lolz_habit_kb(habit, done=done),
    )


@router.callback_query(F.data.startswith("lz:rm:"))
async def cb_lolz_remove(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
) -> None:
    habit = await _owned(callback, session, db_user)
    if habit is None:
        return
    service = LolzService(session)
    await service.deactivate(habit)
    await callback.answer("Убрано")
    await render_lolz_home(callback.message, session, db_user, edit=True)


@router.callback_query(F.data == "lz:mine")
async def cb_lolz_mine(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
) -> None:
    service = LolzService(session)
    habits = await service.list_user_habits(db_user.id)
    await callback.answer()
    if not habits:
        await safe_edit(
            callback.message,
            "Пока нет активных Lolzteam-привычек.",
            reply_markup=lolz_add_kb(),
        )
        return
    await safe_edit(
        callback.message,
        "<b>Мои Lolzteam-привычки</b>",
        reply_markup=lolz_mine_kb(habits),
    )


@router.callback_query(F.data == "lz:custom")
async def cb_lolz_custom(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddLolzCustom.title)
    await callback.answer()
    await safe_edit(
        callback.message,
        "Название своей привычки.\nНапример: <i>Зайти на форум вечером</i>\n\n/cancel — отмена",
        reply_markup=lolz_custom_cancel_kb(),
    )


@router.callback_query(F.data == "lz:cancel")
async def cb_lolz_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer("Отменено")
    await safe_edit(
        callback.message,
        "Создание отменено.",
        reply_markup=lolz_add_kb(),
    )


@router.message(AddLolzCustom.title)
async def lolz_custom_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title or title.startswith("/"):
        await message.answer("Введите название текстом.")
        return
    if not (1 <= len(title) <= 80):
        await message.answer("Название — от 1 до 80 символов.")
        return
    await state.update_data(title=title)
    await state.set_state(AddLolzCustom.emoji)
    await message.answer("Эмодзи для привычки (или «-»).", reply_markup=lolz_custom_cancel_kb())


@router.message(AddLolzCustom.emoji)
async def lolz_custom_emoji(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    emoji = "🌐" if raw in {"-", "нет"} or not raw else raw[:16]
    await state.update_data(emoji=emoji)
    await state.set_state(AddLolzCustom.frequency)
    await message.answer("Как часто выполнять?", reply_markup=lolz_custom_freq_kb())


@router.callback_query(AddLolzCustom.frequency, F.data.startswith("lz:cf:"))
async def lolz_custom_freq(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    db_user: User,
) -> None:
    preset = callback.data.split(":")[-1]
    data = await state.get_data()
    service = LolzService(session)
    await service.create_custom(
        db_user,
        title=str(data.get("title") or "Привычка"),
        emoji=str(data.get("emoji") or "🌐"),
        frequency=FREQ_PRESETS.get(preset, "daily"),
    )
    await state.clear()
    await callback.answer("Создано")
    await render_lolz_home(callback.message, session, db_user, edit=True)


async def _owned(
    callback: CallbackQuery,
    session: AsyncSession,
    user: User,
) -> LolzUserHabit | None:
    raw = callback.data.split(":")[-1] if callback.data else ""
    if not raw.isdigit():
        await callback.answer("Некорректные данные", show_alert=True)
        return None
    habit = await LolzService(session).get_owned(int(raw), user.id)
    if habit is None:
        await callback.answer("Привычка не найдена", show_alert=True)
        return None
    return habit
