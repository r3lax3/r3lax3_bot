"""
Роутер платежей: создание счёта, ожидание, проверка статуса, отмена, оферта (PDF)
"""
import logging
import uuid
from typing import Optional
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.types.input_file import FSInputFile

from src.states.user import UserSG
from src.i18n.translations import translations
from src.keyboards.inline import (
    get_payment_waiting_keyboard,
    get_payment_failed_keyboard,
    get_subscription_detail_keyboard,
)
from src.keyboards.factories import PaymentCallback, RenewCallback, SubscriptionCallback
from src.clients.backend_api import api_client
from src.storage.redis_helper import RedisHelper
from src.utils.formatters import calculate_minutes_until_expiry, format_date
from src.bot.config import config

logger = logging.getLogger(__name__)
router = Router()


async def _show_payment_waiting(
    callback: CallbackQuery,
    language: str,
    payment_id: str,
    expires_at: str,
    pay_link: Optional[str] = None,
    qr_url: Optional[str] = None,
) -> None:
    minutes = calculate_minutes_until_expiry(expires_at)
    text = translations.get("payment.waiting.title", language, minutes=minutes)
    keyboard = get_payment_waiting_keyboard(payment_id, pay_link=pay_link, qr_url=qr_url, language=language)
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(StateFilter(UserSG.STATE_PAYMENT_METHOD_SELECT), PaymentCallback.filter(F.action == "select"))
@router.callback_query(StateFilter(UserSG.STATE_PAYMENT_PENDING), PaymentCallback.filter(F.action == "change_method"))
async def handle_payment_select(
    callback: CallbackQuery,
    state: FSMContext,
    language: str,
    redis_helper: RedisHelper,
    callback_data: PaymentCallback,
):
    """Пользователь выбрал провайдера и план -> создаём платёж"""
    try:
        # Два режима:
        # 1) select: payment_id содержит "<subscription_id>:<provider>:<plan>"
        # 2) change_method: payment_id содержит "<subscription_id>"
        if callback_data.action == "change_method":
            subscription_id = int(callback_data.payment_id)
            subscription = await api_client.get_subscription(subscription_id)
            service_id = subscription.get("service_id")
            options = await api_client.get_service_payment_options(service_id)
            providers = options.get("providers", [])
            plans = options.get("plans", [])
            text = translations.get("payment.method_select.title", language)
            keyboard = get_payment_method_select_keyboard(providers, plans, subscription_id, language)
            await callback.message.edit_text(text, reply_markup=keyboard)
            await state.set_state(UserSG.STATE_PAYMENT_METHOD_SELECT)
            await callback.answer()
            return

        parts = (callback_data.payment_id or "").split(":")
        if len(parts) != 3:
            await callback.answer(translations.get("error.service_unavailable", language), show_alert=True)
            return
        subscription_id = int(parts[0])
        provider = parts[1]
        plan = parts[2]

        # Получаем сервис по подписке
        subscription = await api_client.get_subscription(subscription_id)
        service_id = subscription.get("service_id")
        tg_id = callback.from_user.id

        # Создаём платёж через API (с идемпотентным ключом)
        idempotency_key = str(uuid.uuid4())
        payment = await api_client.create_payment(
            tg_id=tg_id,
            service_id=service_id,
            plan=plan,
            provider=provider,
            idempotency_key=idempotency_key,
        )

        payment_id = payment.get("payment_id")
        pay_link = payment.get("pay_link") or payment.get("link")
        qr_url = payment.get("qr") or payment.get("qr_url")
        expires_at = payment.get("expires_at")

        if not payment_id or not expires_at:
            await callback.answer(translations.get("error.service_unavailable", language), show_alert=True)
            return

        # Сохраняем контекст оплаты
        await redis_helper.set_payment_context(payment_id, tg_id, subscription_id, callback.message.message_id)

        # Показываем экран ожидания оплаты
        await _show_payment_waiting(
            callback,
            language=language,
            payment_id=payment_id,
            expires_at=expires_at,
            pay_link=pay_link,
            qr_url=qr_url,
        )
        await state.set_state(UserSG.STATE_PAYMENT_PENDING)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error creating payment: {e}")
        await callback.answer(translations.get("error.service_unavailable", language), show_alert=True)


@router.callback_query(StateFilter(UserSG.STATE_PAYMENT_PENDING), PaymentCallback.filter(F.action.in_({"check", "cancel", "terms"})))
async def handle_payment_actions(
    callback: CallbackQuery,
    state: FSMContext,
    language: str,
    redis_helper: RedisHelper,
    callback_data: PaymentCallback,
):
    """Обработка кнопок: Проверить статус / Отмена / Открыть счёт (url)"""
    try:
        action = callback_data.action
        payment_id = callback_data.payment_id

        if action == "check":
            # Получаем статус платежа
            payment = await api_client.get_payment(payment_id)
            status = payment.get("status")
            if status in ("created", "pending"):
                # Обновляем таймер до истечения
                expires_at = payment.get("expires_at")
                pay_link = payment.get("pay_link") or payment.get("link")
                qr_url = payment.get("qr") or payment.get("qr_url")
                if expires_at:
                    await _show_payment_waiting(
                        callback,
                        language=language,
                        payment_id=payment_id,
                        expires_at=expires_at,
                        pay_link=pay_link,
                        qr_url=qr_url,
                    )
                await callback.answer()
                return
            elif status == "paid":
                # Оплачено — показываем успех и возвращаемся в карточку подписки
                context = await redis_helper.get_payment_context(payment_id)
                subscription_id = context.get("subscription_id") if context else None
                if not subscription_id:
                    await callback.answer(translations.get("error.service_unavailable", language), show_alert=True)
                    return
                # Обновляем подписку и показываем дату
                subscription = await api_client.get_subscription(subscription_id)
                until = subscription.get("until_date")
                until_text = format_date(until, language) if until else "—"
                success_text = translations.get("payment.success.title", language, until_date=until_text)
                keyboard = get_subscription_detail_keyboard(subscription_id, language)
                await callback.message.edit_text(success_text, reply_markup=keyboard)
                await state.set_state(UserSG.STATE_SUBSCRIPTION_DETAIL)
                await callback.answer()
                return
            else:
                # Неуспех
                context = await redis_helper.get_payment_context(payment_id)
                subscription_id = context.get("subscription_id") if context else None
                if not subscription_id:
                    await callback.answer(translations.get("error.service_unavailable", language), show_alert=True)
                    return
                failed_text = translations.get("payment.failed.title", language)
                keyboard = get_payment_failed_keyboard(payment_id, subscription_id, language)
                await callback.message.edit_text(failed_text, reply_markup=keyboard)
                await callback.answer()
                return

        elif action == "cancel":
            # Отмена: чистим контекст и возвращаемся в карточку подписки
            context = await redis_helper.get_payment_context(payment_id)
            subscription_id = context.get("subscription_id") if context else None
            await redis_helper.clear_payment_context(payment_id)
            if subscription_id:
                # Показать карточку подписки
                try:
                    subscription = await api_client.get_subscription(subscription_id)
                    service_name = subscription.get("service_name", "")
                    until_date = subscription.get("until_date")
                    if until_date:
                        until_text = format_date(until_date, language)
                        text = translations.get("subscriptions.detail.title", language, service_name=service_name, until_date=until_text)
                    else:
                        text = translations.get("subscriptions.detail.expired", language, service_name=service_name)
                except Exception:
                    text = translations.get("menu.main.title", language)
                keyboard = get_subscription_detail_keyboard(subscription_id, language)
                await callback.message.edit_text(text, reply_markup=keyboard)
                await state.set_state(UserSG.STATE_SUBSCRIPTION_DETAIL)
            await callback.answer()
            return

        elif action == "terms":
            # Отправка оферты (PDF) для сервиса выбранной подписки
            # payment_id здесь несёт subscription_id в нашем UX
            try:
                subscription_id = int(payment_id)
            except Exception:
                await callback.answer()
                return
            subscription = await api_client.get_subscription(subscription_id)
            service_id = subscription.get("service_id")
            base_dir = config.offers_dir.rstrip('/')
            file_path = f"{base_dir}/service_{service_id}.pdf"
            try:
                doc = FSInputFile(file_path)
                await callback.message.answer_document(document=doc, caption=translations.get("offers.pdf.title", language))
            except Exception:
                from src.bot.config import config as bot_config
                await callback.message.answer(
                    translations.get("offers.pdf.unavailable", language) + f"\n{bot_config.support_link}"
                )
            await callback.answer()
            return

    except Exception as e:
        logger.error(f"Error in payment actions: {e}")
        await callback.answer(translations.get("error.service_unavailable", language), show_alert=True)
