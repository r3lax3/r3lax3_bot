"""
Middleware для бота
"""
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from src.bot.config import config
from src.clients.backend_api import api_client
from src.storage.redis_helper import RedisHelper
from src.i18n.translations import translations


class LanguageMiddleware(BaseMiddleware):
    """Middleware для определения языка пользователя"""
    
    def __init__(self, redis_helper: RedisHelper):
        super().__init__()
        self.redis_helper = redis_helper
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Получаем tg_id из события
        tg_id = None
        if isinstance(event, Message):
            tg_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            tg_id = event.from_user.id
        
        if tg_id:
            # Пытаемся получить язык из кеша Redis
            language = await self.redis_helper.get_user_language(tg_id)
            
            if not language:
                try:
                    # Если нет в кеше, запрашиваем из API
                    user_data = await api_client.get_user(tg_id)
                    language = user_data.get("language", config.default_language)
                    
                    # Сохраняем в кеш
                    await self.redis_helper.set_user_language(tg_id, language)
                except Exception:
                    # В случае ошибки используем язык по умолчанию
                    language = config.default_language
            
            # Добавляем язык в данные
            data["language"] = language
            
            # Проверяем, является ли пользователь админом
            is_admin = tg_id in config.admin_user_ids
            data["is_admin"] = is_admin
        
        return await handler(event, data)


class ErrorHandlingMiddleware(BaseMiddleware):
    """Middleware для обработки ошибок"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            # Логируем ошибку
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in handler: {e}", exc_info=True)
            
            # Отправляем сообщение об ошибке пользователю
            language = data.get("language", "ru")
            error_message = translations.get("error.service_unavailable", language)
            
            if isinstance(event, Message):
                await event.answer(error_message)
            elif isinstance(event, CallbackQuery):
                await event.answer(error_message, show_alert=True)
            
            return None


class RateLimitMiddleware(BaseMiddleware):
    """Middleware для ограничения скорости запросов"""
    
    def __init__(self, redis_helper: RedisHelper):
        super().__init__()
        self.redis_helper = redis_helper
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Получаем tg_id
        tg_id = None
        if isinstance(event, Message):
            tg_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            tg_id = event.from_user.id
        
        if tg_id:
            # Проверяем rate limit (простая реализация)
            rate_key = f"rate_limit:{tg_id}"
            current_count = await self.redis_helper.redis.get(rate_key)
            
            if current_count and int(current_count) > 10:  # Максимум 10 запросов в минуту
                language = data.get("language", "ru")
                error_message = translations.get("error.service_unavailable", language)
                
                if isinstance(event, Message):
                    await event.answer(error_message)
                elif isinstance(event, CallbackQuery):
                    await event.answer(error_message, show_alert=True)
                
                return None
            
            # Увеличиваем счетчик
            await self.redis_helper.redis.incr(rate_key)
            await self.redis_helper.redis.expire(rate_key, 60)  # TTL 1 минута
        
        return await handler(event, data)
