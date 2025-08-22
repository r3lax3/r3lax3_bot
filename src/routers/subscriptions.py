"""
Роутер подписок: список, деталь, продление (вход)
"""
import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery

from src.states.user import UserSG
from src.i18n.translations import translations
from src.keyboards.inline import (
    get_subscriptions_list_keyboard,
    get_subscription_detail_keyboard,
    get_payment_method_select_keyboard,
)
from src.keyboards.factories import SubscriptionCallback, RenewCallback, PaymentCallback
from src.clients.backend_api import api_client
from src.utils.formatters import format_date

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(StateFilter(UserSG.STATE_SUBSCRIPTIONS_LIST), SubscriptionCallback.filter(F.action == "list"))
async def subscriptions_pagination(callback: CallbackQuery, state: FSMContext, language: str, callback_data: SubscriptionCallback):
    """Пагинация списка подписок"""
    try:
        page = max(1, callback_data.page or 1)
        
        subs_data = await api_client.get_user_subscriptions(callback.from_user.id, page=page)
        items = subs_data.get("items", [])
        pages = subs_data.get("pages", 1)
        
        if not items:
            await callback.answer()
            return
        
        text = translations.get("subscriptions.list.title", language)
        keyboard = get_subscriptions_list_keyboard(items, page, pages, language)
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in subscriptions pagination: {e}")
        await callback.answer(translations.get("error.service_unavailable", language), show_alert=True)


@router.callback_query(StateFilter(UserSG.STATE_SUBSCRIPTIONS_LIST), SubscriptionCallback.filter(F.action == "detail"))
@router.callback_query(StateFilter(UserSG.STATE_IDLE), SubscriptionCallback.filter(F.action == "detail"))
async def open_subscription_detail(callback: CallbackQuery, state: FSMContext, language: str, callback_data: SubscriptionCallback):
    """Открыть деталь подписки"""
    try:
        sub = await api_client.get_subscription(callback_data.subscription_id)
        service_name = sub.get("service_name", "")
        until_date = sub.get("until_date")
        status = sub.get("status")
        
        if until_date:
            until_text = format_date(until_date, language)
            text = translations.get("subscriptions.detail.title", language, service_name=service_name, until_date=until_text)
        else:
            text = translations.get("subscriptions.detail.expired", language, service_name=service_name)
        
        keyboard = get_subscription_detail_keyboard(callback_data.subscription_id, language)
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await state.set_state(UserSG.STATE_SUBSCRIPTION_DETAIL)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error open subscription detail: {e}")
        await callback.answer(translations.get("error.service_unavailable", language), show_alert=True)


@router.callback_query(StateFilter(UserSG.STATE_SUBSCRIPTION_DETAIL), RenewCallback.filter())
async def start_renew_flow(callback: CallbackQuery, state: FSMContext, language: str, callback_data: RenewCallback):
    """Начать продление: загрузить способы оплаты и планы"""
    try:
        subscription_id = callback_data.subscription_id
        sub = await api_client.get_subscription(subscription_id)
        service_id = sub.get("service_id")
        options = await api_client.get_service_payment_options(service_id)
        providers = options.get("providers", [])
        plans = options.get("plans", [])
        
        text = translations.get("payment.method_select.title", language)
        keyboard = get_payment_method_select_keyboard(providers, plans, subscription_id, language)
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await state.set_state(UserSG.STATE_PAYMENT_METHOD_SELECT)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error start renew flow: {e}")
        await callback.answer(translations.get("error.service_unavailable", language), show_alert=True)
