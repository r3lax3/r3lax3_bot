"""
Admin utilities: user profile, search, create/extend subscription
"""
import logging
from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from src.i18n.translations import translations
from src.clients.backend_api import api_client
from src.keyboards.factories import AdminExtendCallback
from src.utils.formatters import format_date
from src.states.admin import AdminSG

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
        text = translations.get(
            "admin.users.profile", language, tg_id=tg_id, language=profile.get("language", "-"), subscriptions_count=len(subs)
        )
        for s in subs[:5]:
            text += f"\n - sub#{s.get('id')} {s.get('service_name')} until: {format_date(s.get('until_date'), language) if s.get('until_date') else '-'}"
        await message.answer(text)
    except Exception as e:
        logger.error(f"admin user profile error: {e}")
        await message.answer(translations.get("error.service_unavailable", language))


@router.message(Command("admin_extend"))
async def admin_extend_cmd(message: Message, is_admin: bool, language: str):
    if not is_admin:
        return
    try:
        parts = message.text.strip().split()
        if len(parts) < 2:
            await message.answer("/admin_extend <subscription_id>")
            return
        subscription_id = int(parts[1])
        sub = await api_client.get_subscription(subscription_id)
        service_id = sub.get("service_id")
        options = await api_client.get_service_payment_options(service_id)
        plans = options.get("plans", [])
        rows = []
        for plan in plans:
            code = plan.get("code")
            amount = plan.get("amount")
            currency = plan.get("currency")
            rows.append([
                InlineKeyboardButton(
                    text=f"{code} {amount} {currency}",
                    callback_data=AdminExtendCallback(action="select_plan", subscription_id=subscription_id, plan=code).pack(),
                )
            ])
        kb = InlineKeyboardMarkup(inline_keyboard=rows)
        await message.answer(translations.get("admin.extend.select_plan", language), reply_markup=kb)
    except Exception as e:
        logger.error(f"admin extend cmd error: {e}")
        await message.answer(translations.get("error.service_unavailable", language))


@router.callback_query(AdminExtendCallback.filter(lambda d: d.action == "select_plan"))
async def admin_extend_select_plan(callback: CallbackQuery, callback_data: AdminExtendCallback, is_admin: bool, language: str):
    if not is_admin:
        return
    text = ("Extend subscription" if language == "en" else "Подтвердите продление") + f" #{callback_data.subscription_id} plan {callback_data.plan}?"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=("Yes" if language == "en" else "Да"),
                    callback_data=AdminExtendCallback(action="confirm", subscription_id=callback_data.subscription_id, plan=callback_data.plan).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text=("No" if language == "en" else "Нет"),
                    callback_data=AdminExtendCallback(action="cancel", subscription_id=callback_data.subscription_id, plan=callback_data.plan).pack(),
                )
            ],
        ]
    )
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(AdminExtendCallback.filter(lambda d: d.action == "confirm"))
async def admin_extend_confirm(callback: CallbackQuery, callback_data: AdminExtendCallback, is_admin: bool, language: str):
    if not is_admin:
        return
    try:
        await api_client.extend_subscription(callback_data.subscription_id, callback_data.plan)
        await callback.message.edit_text("Extended" if language == "en" else "Продлено")
        await callback.answer()
    except Exception as e:
        logger.error(f"admin extend confirm error: {e}")
        await callback.answer(translations.get("error.service_unavailable", language), show_alert=True)


@router.callback_query(AdminExtendCallback.filter(lambda d: d.action == "cancel"))
async def admin_extend_cancel(callback: CallbackQuery, is_admin: bool, language: str):
    if not is_admin:
        return
    await callback.message.edit_text("Canceled" if language == "en" else "Отменено")
    await callback.answer()


@router.message(Command("admin_create_sub"))
async def admin_create_subscription_cmd(message: Message, is_admin: bool, language: str):
    if not is_admin:
        return
    try:
        parts = message.text.strip().split()
        if len(parts) < 4:
            await message.answer("/admin_create_sub <tg_id> <service_id> <plan>")
            return
        tg_id = int(parts[1])
        service_id = int(parts[2])
        plan = parts[3]
        await api_client.create_subscription(tg_id=tg_id, service_id=service_id, plan=plan)
        await message.answer("Done" if language == "en" else "Готово")
    except Exception as e:
        logger.error(f"admin create sub error: {e}")
        await message.answer(translations.get("error.service_unavailable", language))


@router.message(StateFilter(AdminSG.STATE_ADMIN_USER_SEARCH))
async def admin_user_search(message: Message, is_admin: bool, language: str, state: FSMContext):
    if not is_admin:
        return
    try:
        users = await api_client.search_users(message.text.strip())
        if not users:
            await message.answer(translations.get("admin.users.not_found", language))
            return
        lines = ["Use: /admin_user <tg_id>\n"]
        for u in users[:5]:
            line = f"tg_id={u.get('tg_id')} @" + str(u.get('username', '')) + " " + str(u.get('name', ''))
            lines.append(line)
        await message.answer("\n".join(lines))
    except Exception as e:
        logger.error(f"admin user search error: {e}")
        await message.answer(translations.get("error.service_unavailable", language))


