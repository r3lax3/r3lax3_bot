"""
Admin main menu actions via MagicFilter
"""
import logging
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from src.states.admin import AdminSG
from src.i18n.translations import translations
from src.keyboards.inline import get_admin_main_keyboard
from src.keyboards.factories import AdminCallback
from src.clients.backend_api import api_client

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(StateFilter(AdminSG.STATE_ADMIN_MAIN), AdminCallback.filter(F.action == "broadcast"))
async def on_broadcast_selected(callback: CallbackQuery, is_admin: bool, language: str, state: FSMContext):
    if not is_admin:
        return
    await state.set_state(AdminSG.STATE_ADMIN_BROADCAST_TEXT)
    await callback.message.edit_text(translations.get("admin.broadcast.enter_text", language))
    await callback.answer()


@router.callback_query(StateFilter(AdminSG.STATE_ADMIN_MAIN), AdminCallback.filter(F.action == "users"))
async def on_users_selected(callback: CallbackQuery, is_admin: bool, language: str, state: FSMContext):
    if not is_admin:
        return
    await state.set_state(AdminSG.STATE_ADMIN_USER_SEARCH)
    await callback.message.edit_text(translations.get("admin.users.search", language))
    await callback.answer()


@router.callback_query(StateFilter(AdminSG.STATE_ADMIN_MAIN), AdminCallback.filter(F.action == "stats"))
async def on_stats_selected(callback: CallbackQuery, is_admin: bool, language: str):
    if not is_admin:
        return
    try:
        stats = await api_client.get_admin_stats()
        text = translations.get("admin.stats.title", language)
        text += "\n" + translations.get("admin.stats.users_total", language, total=stats.get("users_total", 0))
        text += "\n" + translations.get("admin.stats.users_active", language, active=stats.get("users_active", 0))
        text += "\n" + translations.get("admin.stats.subscriptions_active", language, active=stats.get("subs_active", 0))
        text += "\n" + translations.get(
            "admin.stats.monthly_revenue", language, amount=stats.get("mrr_amount", 0), currency=stats.get("currency", "USD")
        )
        await callback.message.edit_text(text, reply_markup=get_admin_main_keyboard(language))
        await callback.answer()
    except Exception as e:
        logger.error(f"admin stats error: {e}")
        await callback.answer(translations.get("error.service_unavailable", language), show_alert=True)


@router.callback_query(StateFilter(AdminSG.STATE_ADMIN_MAIN), AdminCallback.filter(F.action == "services"))
async def on_services_selected(callback: CallbackQuery, is_admin: bool, language: str):
    if not is_admin:
        return
    hint = "/admin_service <service_id>" if language == "en" else "/admin_service <service_id> — посмотреть и управлять"
    await callback.message.edit_text(hint, reply_markup=get_admin_main_keyboard(language))
    await callback.answer()


