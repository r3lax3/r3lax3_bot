"""
Admin service info and actions
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from src.i18n.translations import translations
from src.keyboards.factories import AdminServiceCallback
from src.clients.backend_api import api_client

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("admin_service"))
async def admin_service_cmd(message: Message, is_admin: bool, language: str):
    if not is_admin:
        return
    try:
        parts = message.text.strip().split()
        if len(parts) < 2:
            await message.answer("/admin_service <service_id>")
            return
        service_id = int(parts[1])
        svc = await api_client.get_service(service_id)
        text = (
            translations.get("admin.services.title", language)
            + f"\nService #{service_id}: {svc.get('name')} status: {svc.get('status')}"
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Start", callback_data=AdminServiceCallback(action="start", service_id=service_id).pack())],
                [InlineKeyboardButton(text="Pause", callback_data=AdminServiceCallback(action="pause", service_id=service_id).pack())],
                [InlineKeyboardButton(text="Resume", callback_data=AdminServiceCallback(action="resume", service_id=service_id).pack())],
            ]
        )
        await message.answer(text, reply_markup=kb)
    except Exception as e:
        logger.error(f"admin service cmd error: {e}")
        await message.answer(translations.get("error.service_unavailable", language))


@router.callback_query(AdminServiceCallback.filter(F.action == "start"))
async def admin_service_start(callback: CallbackQuery, callback_data: AdminServiceCallback, is_admin: bool, language: str):
    if not is_admin:
        return
    try:
        await api_client.start_service(callback_data.service_id)
        await callback.answer(translations.get("admin.services.start", language))
    except Exception as e:
        logger.error(f"admin service action error: {e}")
        await callback.answer(translations.get("error.service_unavailable", language), show_alert=True)


@router.callback_query(AdminServiceCallback.filter(F.action == "pause"))
async def admin_service_pause(callback: CallbackQuery, callback_data: AdminServiceCallback, is_admin: bool, language: str):
    if not is_admin:
        return
    try:
        await api_client.pause_service(callback_data.service_id)
        await callback.answer(translations.get("admin.services.pause", language))
    except Exception as e:
        logger.error(f"admin service action error: {e}")
        await callback.answer(translations.get("error.service_unavailable", language), show_alert=True)


@router.callback_query(AdminServiceCallback.filter(F.action == "resume"))
async def admin_service_resume(callback: CallbackQuery, callback_data: AdminServiceCallback, is_admin: bool, language: str):
    if not is_admin:
        return
    try:
        await api_client.resume_service(callback_data.service_id)
        await callback.answer(translations.get("admin.services.resume", language))
    except Exception as e:
        logger.error(f"admin service action error: {e}")
        await callback.answer(translations.get("error.service_unavailable", language), show_alert=True)


