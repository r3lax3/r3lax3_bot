"""
Admin broadcast flow using MagicFilter
"""
import logging
import asyncio
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.states.admin import AdminSG
from src.i18n.translations import translations
from src.keyboards.inline import get_admin_main_keyboard
from src.storage.redis_helper import RedisHelper
from src.clients.backend_api import api_client
from src.bot.config import config

logger = logging.getLogger(__name__)
router = Router()


@router.message(StateFilter(AdminSG.STATE_ADMIN_BROADCAST_TEXT))
async def set_broadcast_text(message: Message, state: FSMContext, is_admin: bool, language: str, redis_helper: RedisHelper):
    if not is_admin:
        return
    await redis_helper.set_broadcast_draft(message.from_user.id, message.text)
    await state.set_state(AdminSG.STATE_ADMIN_BROADCAST_SEGMENT)
    text = translations.get("admin.broadcast.select_segment", language)
    await message.answer(text + "\n- all\n- active_subs\n- no_active_subs\n- service:<id>")


@router.message(StateFilter(AdminSG.STATE_ADMIN_BROADCAST_SEGMENT))
async def set_broadcast_segment(message: Message, state: FSMContext, is_admin: bool, language: str, redis_helper: RedisHelper):
    if not is_admin:
        return
    segment = message.text.strip()
    draft = await redis_helper.get_broadcast_draft(message.from_user.id) or {}
    await redis_helper.set_broadcast_draft(message.from_user.id, draft.get("text", ""), segment=segment)
    await state.set_state(AdminSG.STATE_ADMIN_BROADCAST_PREVIEW)
    preview = translations.get("admin.broadcast.preview", language, text=draft.get("text", ""), segment=segment)
    await message.answer(preview + "\n\n" + ("Yes/No" if language == "en" else "Да/Нет"))


@router.message(StateFilter(AdminSG.STATE_ADMIN_BROADCAST_PREVIEW), F.text.lower().in_({"yes", "да", "y"}))
async def confirm_broadcast_yes(message: Message, state: FSMContext, is_admin: bool, language: str, redis_helper: RedisHelper):
    if not is_admin:
        return
    await message.answer(translations.get("admin.broadcast.sending", language))
    draft = await redis_helper.get_broadcast_draft(message.from_user.id) or {}
    segment = draft.get("segment", "all")
    text = draft.get("text", "")

    delivered = 0
    failed = 0
    cursor = None
    limit = config.broadcast_batch_size
    try:
        while True:
            resp = await api_client.get_broadcast_recipients(segment, cursor=cursor, limit=limit)
            ids = resp.get("items", [])
            if not ids:
                break
            rps = config.telegram_delivery_rps
            for i, uid in enumerate(ids):
                try:
                    await message.bot.send_message(chat_id=uid, text=text)
                    delivered += 1
                except Exception:
                    failed += 1
                if (i + 1) % rps == 0:
                    await asyncio.sleep(1)
            cursor = resp.get("next_cursor")
            if not cursor:
                break
    except Exception as e:
        logger.error(f"broadcast error: {e}")
    await redis_helper.clear_broadcast_draft(message.from_user.id)
    report = translations.get("admin.broadcast.complete", language, delivered=delivered, failed=failed, skipped=0)
    await message.answer(report, reply_markup=get_admin_main_keyboard(language))
    await state.set_state(AdminSG.STATE_ADMIN_MAIN)


@router.message(StateFilter(AdminSG.STATE_ADMIN_BROADCAST_PREVIEW))
async def confirm_broadcast_no(message: Message, state: FSMContext, is_admin: bool, language: str):
    if not is_admin:
        return
    await state.set_state(AdminSG.STATE_ADMIN_MAIN)
    await message.answer(translations.get("admin.broadcast.confirm.no", language), reply_markup=get_admin_main_keyboard(language))


