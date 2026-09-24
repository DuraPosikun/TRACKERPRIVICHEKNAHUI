from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.models import LolzTemplate
from keyboards.lolz import (
    admin_lolz_cats_kb,
    admin_lolz_delete_kb,
    admin_lolz_freq_kb,
    admin_lolz_item_kb,
    admin_lolz_list_kb,
    admin_lolz_new_cats_kb,
    admin_lolz_new_freq_kb,
    admin_lolz_cancel_kb,
)
from services.lolz_catalog import CATEGORIES, FREQ_LABELS
from services.lolz_service import LolzService
from states.lolz import AdminLolzTemplate
from utils.formatters import escape, safe_edit

router = Router(name="admin_lolz")


def _is_admin(telegram_id: int) -> bool:
    return settings.admin_id is not None and telegram_id == settings.admin_id


async def _guard(callback: CallbackQuery) -> bool:
    if _is_admin(callback.from_user.id):
        return True
    await callback.answer("Нет доступа", show_alert=True)
    return False


def _tpl_text(template: LolzTemplate) -> str:
    status = "активен" if template.is_active else "отключён"
    return (
        f"{template.emoji} <b>{escape(template.title)}</b>\n\n"
        f"{escape(template.description or '—')}\n\n"
        f"Код: <code>{escape(template.code)}</code>\n"
        f"Категория: {CATEGORIES.get(template.category, template.category)}\n"
        f"Периодичность: {FREQ_LABELS.get(template.recommended_frequency, template.recommended_frequency)}\n"
        f"Статус: {status}"
    )


@router.callback_query(F.data == "alz:list")
async def admin_list(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    if not await _guard(callback):
        return
    await state.clear()
    service = LolzService(session)
    await service.seed_templates()
    templates = await service.list_templates(active_only=False)
    await callback.answer()
    await safe_edit(
        callback.message,
        "<b>🌐 LOLZTEAM ПРИВЫЧКИ</b>\n\nШаблоны общие. Выполнения пользователей здесь не видны.",
        reply_markup=admin_lolz_list_kb(templates),
    )


@router.callback_query(F.data.startswith("alz:v:"))
async def admin_view(callback: CallbackQuery, session: AsyncSession) -> None:
    if not await _guard(callback):
        return
    raw = callback.data.split(":")[-1]
    template = await LolzService(session).get_template(int(raw) if raw.isdigit() else -1)
    if template is None:
        await callback.answer("Не найдено", show_alert=True)
        return
    await callback.answer()
    await safe_edit(callback.message, _tpl_text(template), reply_markup=admin_lolz_item_kb(template))


@router.callback_query(F.data.startswith("alz:tg:"))
async def admin_toggle(callback: CallbackQuery, session: AsyncSession) -> None:
    if not await _guard(callback):
        return
    raw = callback.data.split(":")[-1]
    service = LolzService(session)
    template = await service.get_template(int(raw) if raw.isdigit() else -1)
    if template is None:
        await callback.answer("Не найдено", show_alert=True)
        return
    await service.update_template(template, is_active=not template.is_active)
    await callback.answer("Сохранено")
    await safe_edit(callback.message, _tpl_text(template), reply_markup=admin_lolz_item_kb(template))


@router.callback_query(F.data.startswith("alz:cat:"))
async def admin_cat_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    if not await _guard(callback):
        return
    raw = callback.data.split(":")[-1]
    template = await LolzService(session).get_template(int(raw) if raw.isdigit() else -1)
    if template is None:
        await callback.answer("Не найдено", show_alert=True)
        return
    await callback.answer()
    await safe_edit(
        callback.message,
        "Новая категория шаблона:",
        reply_markup=admin_lolz_cats_kb(template.id),
    )


@router.callback_query(F.data.startswith("alz:cs:"))
async def admin_cat_set(callback: CallbackQuery, session: AsyncSession) -> None:
    if not await _guard(callback):
        return
    parts = callback.data.split(":")
    if len(parts) != 4 or not parts[2].isdigit():
        await callback.answer()
        return
    service = LolzService(session)
    template = await service.get_template(int(parts[2]))
    if template is None:
        await callback.answer("Не найдено", show_alert=True)
        return
    await service.update_template(template, category=parts[3])
    await callback.answer("Категория обновлена")
    await safe_edit(callback.message, _tpl_text(template), reply_markup=admin_lolz_item_kb(template))


@router.callback_query(F.data.startswith("alz:fr:"))
async def admin_freq_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    if not await _guard(callback):
        return
    raw = callback.data.split(":")[-1]
    template = await LolzService(session).get_template(int(raw) if raw.isdigit() else -1)
    if template is None:
        await callback.answer("Не найдено", show_alert=True)
        return
    await callback.answer()
    await safe_edit(
        callback.message,
        "Рекомендуемая периодичность:",
        reply_markup=admin_lolz_freq_kb(template.id),
    )


@router.callback_query(F.data.startswith("alz:fs:"))
async def admin_freq_set(callback: CallbackQuery, session: AsyncSession) -> None:
    if not await _guard(callback):
        return
    parts = callback.data.split(":")
    if len(parts) != 4 or not parts[2].isdigit():
        await callback.answer()
        return
    service = LolzService(session)
    template = await service.get_template(int(parts[2]))
    if template is None:
        await callback.answer("Не найдено", show_alert=True)
        return
    await service.update_template(template, recommended_frequency=parts[3])
    await callback.answer("Сохранено")
    await safe_edit(callback.message, _tpl_text(template), reply_markup=admin_lolz_item_kb(template))


@router.callback_query(F.data.startswith("alz:ren:"))
async def admin_rename_start(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    if not await _guard(callback):
        return
    raw = callback.data.split(":")[-1]
    template = await LolzService(session).get_template(int(raw) if raw.isdigit() else -1)
    if template is None:
        await callback.answer("Не найдено", show_alert=True)
        return
    await state.set_state(AdminLolzTemplate.rename)
    await state.update_data(template_id=template.id)
    await callback.answer()
    await safe_edit(
        callback.message,
        "Новое название шаблона:",
        reply_markup=admin_lolz_cancel_kb(),
    )


@router.message(AdminLolzTemplate.rename)
async def admin_rename_save(message: Message, state: FSMContext, session: AsyncSession) -> None:
    if not _is_admin(message.from_user.id):
        await state.clear()
        return
    title = (message.text or "").strip()
    if not (1 <= len(title) <= 80):
        await message.answer("Название — от 1 до 80 символов.")
        return
    data = await state.get_data()
    service = LolzService(session)
    template = await service.get_template(int(data.get("template_id") or 0))
    await state.clear()
    if template is None:
        await message.answer("Шаблон не найден.")
        return
    await service.update_template(template, title=title)
    await message.answer(_tpl_text(template), parse_mode="HTML", reply_markup=admin_lolz_item_kb(template))


@router.callback_query(F.data.startswith("alz:dl:"))
async def admin_delete_ask(callback: CallbackQuery, session: AsyncSession) -> None:
    if not await _guard(callback):
        return
    raw = callback.data.split(":")[-1]
    template = await LolzService(session).get_template(int(raw) if raw.isdigit() else -1)
    if template is None:
        await callback.answer("Не найдено", show_alert=True)
        return
    await callback.answer()
    await safe_edit(
        callback.message,
        f"Удалить шаблон {template.emoji} <b>{escape(template.title)}</b>?",
        reply_markup=admin_lolz_delete_kb(template.id),
    )


@router.callback_query(F.data.startswith("alz:dx:"))
async def admin_delete_ok(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    if not await _guard(callback):
        return
    raw = callback.data.split(":")[-1]
    service = LolzService(session)
    template = await service.get_template(int(raw) if raw.isdigit() else -1)
    if template is None:
        await callback.answer("Не найдено", show_alert=True)
        return
    await service.delete_template(template)
    await state.clear()
    templates = await service.list_templates(active_only=False)
    await callback.answer("Удалено")
    await safe_edit(
        callback.message,
        "<b>🌐 LOLZTEAM ПРИВЫЧКИ</b>\n\nШаблон удалён.",
        reply_markup=admin_lolz_list_kb(templates),
    )


@router.callback_query(F.data == "alz:new")
async def admin_new(callback: CallbackQuery, state: FSMContext) -> None:
    if not await _guard(callback):
        return
    await state.set_state(AdminLolzTemplate.title)
    await callback.answer()
    await safe_edit(
        callback.message,
        "Название нового шаблона:",
        reply_markup=admin_lolz_cancel_kb(),
    )


@router.message(AdminLolzTemplate.title)
async def admin_new_title(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        await state.clear()
        return
    title = (message.text or "").strip()
    if not (1 <= len(title) <= 80):
        await message.answer("Название — от 1 до 80 символов.")
        return
    await state.update_data(title=title)
    await state.set_state(AdminLolzTemplate.emoji)
    await message.answer("Эмодзи шаблона:", reply_markup=admin_lolz_cancel_kb())


@router.message(AdminLolzTemplate.emoji)
async def admin_new_emoji(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        await state.clear()
        return
    emoji = (message.text or "🌐").strip()[:16]
    await state.update_data(emoji=emoji)
    await state.set_state(AdminLolzTemplate.category)
    await message.answer("Категория:", reply_markup=admin_lolz_new_cats_kb())


@router.callback_query(AdminLolzTemplate.category, F.data.startswith("alz:nc:"))
async def admin_new_cat(callback: CallbackQuery, state: FSMContext) -> None:
    if not await _guard(callback):
        return
    await state.update_data(category=callback.data.split(":")[-1])
    await state.set_state(AdminLolzTemplate.frequency)
    await callback.answer()
    await safe_edit(
        callback.message,
        "Рекомендуемая периодичность:",
        reply_markup=admin_lolz_new_freq_kb(),
    )


@router.callback_query(AdminLolzTemplate.frequency, F.data.startswith("alz:nf:"))
async def admin_new_freq(callback: CallbackQuery, state: FSMContext) -> None:
    if not await _guard(callback):
        return
    await state.update_data(recommended_frequency=callback.data.split(":")[-1])
    await state.set_state(AdminLolzTemplate.description)
    await callback.answer()
    await safe_edit(
        callback.message,
        "Короткое описание или «-».",
        reply_markup=admin_lolz_cancel_kb(),
    )


@router.message(AdminLolzTemplate.description)
async def admin_new_desc(message: Message, state: FSMContext, session: AsyncSession) -> None:
    if not _is_admin(message.from_user.id):
        await state.clear()
        return
    raw = (message.text or "").strip()
    desc = None if raw in {"-", "нет"} else raw[:500]
    data = await state.get_data()
    service = LolzService(session)
    template = await service.create_template(
        title=str(data.get("title") or "Шаблон"),
        emoji=str(data.get("emoji") or "🌐"),
        category=str(data.get("category") or "chat"),
        recommended_frequency=str(data.get("recommended_frequency") or "daily"),
        description=desc,
    )
    await state.clear()
    await message.answer("Шаблон создан.", parse_mode="HTML", reply_markup=admin_lolz_item_kb(template))
    await message.answer(_tpl_text(template), parse_mode="HTML", reply_markup=admin_lolz_item_kb(template))
