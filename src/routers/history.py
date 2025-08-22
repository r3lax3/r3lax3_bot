"""
Роутер истории платежей: пагинация списка и деталь платежа
"""
import logging
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from src.states.user import UserSG
from src.i18n.translations import translations
from src.keyboards.inline import get_payments_history_keyboard
from src.keyboards.factories import PaymentHistoryCallback, PaymentDetailCallback
from src.clients.backend_api import api_client
from src.utils.formatters import format_payment_description

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(StateFilter(UserSG.STATE_PAYMENTS_HISTORY), PaymentHistoryCallback.filter())
async def payments_history_pagination(callback: CallbackQuery, state: FSMContext, language: str, callback_data: PaymentHistoryCallback):
    """Пагинация списка истории платежей"""
    try:
        page = max(1, callback_data.page or 1)
        payments_data = await api_client.get_user_payments(callback.from_user.id, page=page)
        items = payments_data.get("items", [])
        pages = payments_data.get("pages", 1)
        if not items:
            await callback.answer()
            return
        text = translations.get("payments.history.title", language, n=len(items))
        keyboard = get_payments_history_keyboard(items, page, pages, language)
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in payments history pagination: {e}")
        await callback.answer(translations.get("error.service_unavailable", language), show_alert=True)


@router.callback_query(StateFilter(UserSG.STATE_PAYMENTS_HISTORY), PaymentDetailCallback.filter())
@router.callback_query(StateFilter(UserSG.STATE_IDLE), PaymentDetailCallback.filter())
async def payment_detail(callback: CallbackQuery, state: FSMContext, language: str, callback_data: PaymentDetailCallback):
    """Показать деталь платежа"""
    try:
        payment_id = callback_data.payment_id
        payment = await api_client.get_payment(payment_id)
        text = format_payment_description(
            payment_id=payment.get("id"),
            provider=payment.get("provider", ""),
            amount=payment.get("amount", 0),
            currency=payment.get("currency", ""),
            status=payment.get("status", ""),
            date=payment.get("date", ""),
            description=payment.get("description"),
            external_id=payment.get("external_id"),
            language=language,
        )
        await callback.message.edit_text(text)
        await state.set_state(UserSG.STATE_PAYMENT_DETAIL)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in payment detail: {e}")
        await callback.answer(translations.get("error.service_unavailable", language), show_alert=True)
