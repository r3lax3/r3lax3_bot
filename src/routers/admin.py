"""
Админ-роутер: вход, рассылка, пользователи
"""
import logging
import asyncio
from typing import Optional, List
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from src.states.admin import AdminSG
from src.i18n.translations import translations
from src.keyboards.inline import get_admin_main_keyboard
from src.keyboards.factories import AdminCallback, AdminExtendCallback
from src.storage.redis_helper import RedisHelper
from src.clients.backend_api import api_client
from src.utils.formatters import format_date

logger = logging.getLogger(__name__)
router = Router()
@router.message(Command("admin_user"))
async def admin_user_profile_cmd(message: Message, is_admin: bool, language: str):
    if not is_admin:
        return
    try:
        parts = message.text.strip().split()
        if len(parts) < 2:
            await message.answer("/admin_user <tg_id>")
            return
        tg_id = int(parts[1])
        profile = await api_client.get_admin_user(tg_id)
        subs = profile.get("subscriptions", [])
        payments = profile.get("payments", [])
        text = translations.get("admin.users.profile", language, tg_id=tg_id, language=profile.get("language", "-"), subscriptions_count=len(subs))
        # Упростим вывод подписок
        for s in subs[:5]:
            text += f"\n - sub#{s.get('id')} {s.get('service_name')} until: {format_date(s.get('until_date'), language) if s.get('until_date') else '-'}"
        await message.answer(text)
    except Exception as e:
        logger.error(f"admin user profile error: {e}")
        await message.answer(translations.get("error.service_unavailable", language))


@router.message(Command("admin"))
async def admin_entry(message: Message, is_admin: bool, language: str, state: FSMContext):
    if not is_admin:
        return
    await message.answer("Admin Panel" if language == "en" else "Админ-панель", reply_markup=get_admin_main_keyboard(language))
    await state.set_state(AdminSG.STATE_ADMIN_MAIN)


@router.callback_query(StateFilter(AdminSG.STATE_ADMIN_MAIN))
async def admin_main_actions(callback: CallbackQuery, is_admin: bool, language: str, state: FSMContext):
    if not is_admin:
        return
    try:
        data = AdminCallback.unpack(callback.data)
        if data.action == "broadcast":
            await state.set_state(AdminSG.STATE_ADMIN_BROADCAST_TEXT)
            await callback.message.edit_text(translations.get("admin.broadcast.enter_text", language))
            await callback.answer()
        elif data.action == "users":
            await state.set_state(AdminSG.STATE_ADMIN_USER_SEARCH)
            await callback.message.edit_text(translations.get("admin.users.search", language))
            await callback.answer()
        elif data.action == "stats":
            stats = await api_client.get_admin_stats()
            text = translations.get("admin.stats.title", language)
            text += "\n" + translations.get("admin.stats.users_total", language, total=stats.get("users_total", 0))
            text += "\n" + translations.get("admin.stats.users_active", language, active=stats.get("users_active", 0))
            text += "\n" + translations.get("admin.stats.subscriptions_active", language, active=stats.get("subs_active", 0))
            text += "\n" + translations.get("admin.stats.monthly_revenue", language, amount=stats.get("mrr_amount", 0), currency=stats.get("currency", "USD"))
            await callback.message.edit_text(text, reply_markup=get_admin_main_keyboard(language))
            await callback.answer()
        else:
            await callback.answer()
    except Exception as e:
        logger.error(f"admin main error: {e}")
        await callback.answer(translations.get("error.service_unavailable", language), show_alert=True)


# Broadcast flow
@router.message(StateFilter(AdminSG.STATE_ADMIN_BROADCAST_TEXT))
async def admin_broadcast_text(message: Message, state: FSMContext, is_admin: bool, language: str, redis_helper: RedisHelper):
    if not is_admin:
        return
    await redis_helper.set_broadcast_draft(message.from_user.id, message.text)
    await state.set_state(AdminSG.STATE_ADMIN_BROADCAST_SEGMENT)
    text = translations.get("admin.broadcast.select_segment", language)
    await message.answer(text + "\n- all\n- active_subs\n- no_active_subs\n- service:<id>")


@router.message(StateFilter(AdminSG.STATE_ADMIN_BROADCAST_SEGMENT))
async def admin_broadcast_segment(message: Message, state: FSMContext, is_admin: bool, language: str, redis_helper: RedisHelper):
    if not is_admin:
        return
    seg = message.text.strip()
    draft = await redis_helper.get_broadcast_draft(message.from_user.id) or {}
    await redis_helper.set_broadcast_draft(message.from_user.id, draft.get("text", ""), segment=seg)
    await state.set_state(AdminSG.STATE_ADMIN_BROADCAST_PREVIEW)
    preview = translations.get("admin.broadcast.preview", language, text=draft.get("text", ""), segment=seg)
    await message.answer(preview + "\n\n" + ("Yes/No" if language == "en" else "Да/Нет"))


@router.message(StateFilter(AdminSG.STATE_ADMIN_BROADCAST_PREVIEW))
async def admin_broadcast_confirm(message: Message, state: FSMContext, is_admin: bool, language: str, redis_helper: RedisHelper):
    if not is_admin:
        return
    raw = message.text.strip().lower()
    yes_vals = {"yes", "да", "y"}
    if raw not in yes_vals:
        await state.set_state(AdminSG.STATE_ADMIN_MAIN)
        await message.answer(translations.get("admin.broadcast.confirm.no", language), reply_markup=get_admin_main_keyboard(language))
        return
    # Отправка
    await message.answer(translations.get("admin.broadcast.sending", language))
    draft = await redis_helper.get_broadcast_draft(message.from_user.id) or {}
    seg = draft.get("segment", "all")
    text = draft.get("text", "")
    delivered = 0
    failed = 0
    skipped = 0
    cursor = None
    limit = 1000
    try:
        while True:
            resp = await api_client.get_broadcast_recipients(seg, cursor=cursor, limit=limit)
            ids = resp.get("items", [])
            if not ids:
                break
            # Отправляем с ограничением rps
            rps = 20
            for i, uid in enumerate(ids):
                try:
                    await message.bot.send_message(chat_id=uid, text=text)
                    delivered += 1
                except Exception:
                    failed += 1
                # грубый rps контроль
                if (i + 1) % rps == 0:
                    await asyncio.sleep(1)
            cursor = resp.get("next_cursor")
            if not cursor:
                break
    except Exception as e:
        logger.error(f"broadcast error: {e}")
    await redis_helper.clear_broadcast_draft(message.from_user.id)
    report = translations.get("admin.broadcast.complete", language, delivered=delivered, failed=failed, skipped=skipped)
    await message.answer(report, reply_markup=get_admin_main_keyboard(language))
    await state.set_state(AdminSG.STATE_ADMIN_MAIN)


# Users search
@router.message(StateFilter(AdminSG.STATE_ADMIN_USER_SEARCH))
async def admin_user_search(message: Message, is_admin: bool, language: str, state: FSMContext):
    if not is_admin:
        return
    try:
        users = await api_client.search_users(message.text.strip())
        if not users:
            await message.answer(translations.get("admin.users.not_found", language))
            return
        # Покажем первые 5 (tg_id, username, name). Подсказка открыть профиль: /admin_user <tg_id>
        lines = ["Use: /admin_user <tg_id>\n"]
        for u in users[:5]:
            line = f"tg_id={u.get('tg_id')} @" + str(u.get('username', '')) + " " + str(u.get('name', ''))
            lines.append(line)
        await message.answer("\n".join(lines))
    except Exception as e:
        logger.error(f"user search error: {e}")
        await message.answer(translations.get("error.service_unavailable", language))
