"""
Основной роутер пользователя
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State

from src.states.user import UserSG
from src.keyboards.reply import get_main_keyboard, get_admin_main_keyboard
from src.keyboards.inline import get_language_select_keyboard
from src.clients.backend_api import api_client
from src.storage.redis_helper import RedisHelper
from src.i18n.translations import translations
from src.utils.formatters import format_date

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, language: str, is_admin: bool):
    """Обработка команды /start"""
    try:
        # Получаем данные пользователя
        user_data = await api_client.get_user(message.from_user.id)
        used_bot_before = user_data.get("used_bot_before", False)
        
        # Определяем клавиатуру
        if is_admin:
            keyboard = get_admin_main_keyboard(language)
        else:
            keyboard = get_main_keyboard(language)
        
        # Определяем приветственное сообщение
        if not used_bot_before:
            welcome_text = translations.get("welcome.first_time", language)
            # Отмечаем, что пользователь уже использовал бота
            await api_client.update_user(message.from_user.id, used_bot_before=True)
        else:
            welcome_text = translations.get("welcome.returning", language)
        
        # Отправляем приветствие
        await message.answer(
            welcome_text,
            reply_markup=keyboard
        )
        
        # Устанавливаем состояние IDLE
        await state.set_state(UserSG.STATE_IDLE)
        
        # Отправляем событие в телеметрию
        await api_client.send_event("user_start", message.from_user.id)
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        error_message = translations.get("error.service_unavailable", language)
        await message.answer(error_message)


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext, language: str, is_admin: bool):
    """Обработка команды /menu"""
    try:
        # Определяем клавиатуру
        if is_admin:
            keyboard = get_admin_main_keyboard(language)
        else:
            keyboard = get_main_keyboard(language)
        
        # Отправляем главное меню
        await message.answer(
            translations.get("menu.main.title", language),
            reply_markup=keyboard
        )
        
        # Устанавливаем состояние IDLE
        await state.set_state(UserSG.STATE_IDLE)
        
    except Exception as e:
        logger.error(f"Error in menu command: {e}")
        error_message = translations.get("error.service_unavailable", language)
        await message.answer(error_message)


@router.message(StateFilter(UserSG.STATE_IDLE), F.text == "Подписки")
@router.message(StateFilter(UserSG.STATE_IDLE), F.text == "Subscriptions")
async def handle_subscriptions(message: Message, state: FSMContext, language: str):
    """Обработка кнопки 'Подписки'"""
    try:
        # Получаем подписки пользователя
        subscriptions_data = await api_client.get_user_subscriptions(message.from_user.id, page=1)
        subscriptions = subscriptions_data.get("items", [])
        total_pages = subscriptions_data.get("pages", 1)
        
        if not subscriptions:
            # Нет подписок
            await message.answer(
                translations.get("subscriptions.list.empty", language),
                reply_markup=get_main_keyboard(language)
            )
            return
        
        # Формируем список подписок
        subscriptions_text = translations.get("subscriptions.list.title", language)
        
        # Создаем inline клавиатуру для списка подписок
        from src.keyboards.inline import get_subscriptions_list_keyboard
        keyboard = get_subscriptions_list_keyboard(subscriptions, 1, total_pages, language)
        
        await message.answer(
            subscriptions_text,
            reply_markup=keyboard
        )
        
        # Устанавливаем состояние просмотра списка подписок
        await state.set_state(UserSG.STATE_SUBSCRIPTIONS_LIST)
        
    except Exception as e:
        logger.error(f"Error getting subscriptions: {e}")
        error_message = translations.get("error.service_unavailable", language)
        await message.answer(error_message)


@router.message(StateFilter(UserSG.STATE_IDLE), F.text == "История платежей")
@router.message(StateFilter(UserSG.STATE_IDLE), F.text == "Payment history")
async def handle_payment_history(message: Message, state: FSMContext, language: str):
    """Обработка кнопки 'История платежей'"""
    try:
        # Получаем историю платежей
        payments_data = await api_client.get_user_payments(message.from_user.id, page=1)
        payments = payments_data.get("items", [])
        total_pages = payments_data.get("pages", 1)
        
        if not payments:
            # Нет платежей
            await message.answer(
                translations.get("payments.history.empty", language),
                reply_markup=get_main_keyboard(language)
            )
            return
        
        # Формируем текст
        history_text = translations.get("payments.history.title", language, n=len(payments))
        
        # Создаем inline клавиатуру для истории платежей
        from src.keyboards.inline import get_payments_history_keyboard
        keyboard = get_payments_history_keyboard(payments, 1, total_pages, language)
        
        await message.answer(
            history_text,
            reply_markup=keyboard
        )
        
        # Устанавливаем состояние просмотра истории платежей
        await state.set_state(UserSG.STATE_PAYMENTS_HISTORY)
        
    except Exception as e:
        logger.error(f"Error getting payment history: {e}")
        error_message = translations.get("error.service_unavailable", language)
        await message.answer(error_message)


@router.message(Command("lang"))
@router.message(StateFilter(UserSG.STATE_IDLE), F.text.in_({"Смена языка", "Language"}))
async def handle_language_toggle(message: Message, state: FSMContext, language: str, redis_helper: RedisHelper):
    """Мгновенное переключение RU/EN"""
    try:
        new_language = "en" if language == "ru" else "ru"
        await api_client.update_user_language(message.from_user.id, new_language)
        await redis_helper.set_user_language(message.from_user.id, new_language)
        confirmation_text = translations.get(
            f"language.switched.{new_language}", new_language
        )
        await message.answer(confirmation_text, reply_markup=(
            get_admin_main_keyboard(new_language) if message.from_user.id in [] else get_main_keyboard(new_language)
        ))
        await state.set_state(UserSG.STATE_IDLE)
    except Exception as e:
        logger.error(f"Error toggling language: {e}")
        await message.answer(translations.get("error.service_unavailable", language))


@router.message(StateFilter(UserSG.STATE_IDLE), F.text == "Техподдержка")
@router.message(StateFilter(UserSG.STATE_IDLE), F.text == "Support")
async def handle_support(message: Message, language: str):
    """Обработка кнопки 'Техподдержка'"""
    try:
        from src.bot.config import config
        support_text = translations.get("support.title", language, support_link=config.support_link)
        
        await message.answer(support_text)
        
    except Exception as e:
        logger.error(f"Error in support: {e}")
        error_message = translations.get("error.service_unavailable", language)
        await message.answer(error_message)


@router.message(StateFilter(UserSG.STATE_IDLE), F.text == "FAQ")
async def handle_faq(message: Message, state: FSMContext, language: str):
    """Обработка кнопки 'FAQ'"""
    try:
        # TODO: Получить FAQ из API
        faq_text = translations.get("faq.title", language)
        
        # Создаем клавиатуру с кнопкой назад
        from src.keyboards.inline import get_language_select_keyboard
        keyboard = get_language_select_keyboard(language)  # Временно используем языковую клавиатуру
        
        await message.answer(
            faq_text,
            reply_markup=keyboard
        )
        
        # Устанавливаем состояние просмотра FAQ
        await state.set_state(UserSG.STATE_FAQ)
        
    except Exception as e:
        logger.error(f"Error in FAQ: {e}")
        error_message = translations.get("error.service_unavailable", language)
        await message.answer(error_message)


@router.message(StateFilter(UserSG.STATE_IDLE), F.text == "Админ-панель")
@router.message(StateFilter(UserSG.STATE_IDLE), F.text == "Admin Panel")
async def handle_admin_panel(message: Message, state: FSMContext, language: str, is_admin: bool):
    """Обработка кнопки 'Админ-панель'"""
    if not is_admin:
        return  # Игнорируем, если пользователь не админ
    
    try:
        # TODO: Создать админскую клавиатуру
        admin_text = "Админ-панель" if language == "ru" else "Admin Panel"
        
        await message.answer(admin_text)
        
        # TODO: Установить админское состояние
        
    except Exception as e:
        logger.error(f"Error in admin panel: {e}")
        error_message = translations.get("error.service_unavailable", language)
        await message.answer(error_message)


# Обработка callback для смены языка
@router.callback_query(StateFilter(UserSG.STATE_LANGUAGE_SELECT))
async def handle_language_callback(callback: CallbackQuery, state: FSMContext, language: str, redis_helper: RedisHelper):
    """Обработка выбора языка"""
    try:
        from src.keyboards.factories import LanguageCallback
        
        # Парсим callback данные
        data = LanguageCallback.unpack(callback.data)
        new_language = data.language
        
        # Обновляем язык в API
        await api_client.update_user_language(callback.from_user.id, new_language)
        
        # Обновляем язык в кеше Redis (через внедренный redis_helper)
        await redis_helper.set_user_language(callback.from_user.id, new_language)
        
        # Отправляем подтверждение
        confirmation_text = translations.get(f"language.switched.{new_language}", new_language)
        
        await callback.message.edit_text(confirmation_text)
        
        # Возвращаемся в главное меню
        await state.set_state(UserSG.STATE_IDLE)
        
        # Отправляем обновленное главное меню
        keyboard = get_main_keyboard(new_language)
        await callback.message.answer(
            translations.get("menu.main.title", new_language),
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error changing language: {e}")
        error_message = translations.get("error.service_unavailable", language)
        await callback.answer(error_message, show_alert=True)
    
    finally:
        await callback.answer()
