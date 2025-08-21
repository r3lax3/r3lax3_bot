"""
Redis helper для хранения состояния и контекста
"""
import json
from typing import Optional, Any, Dict
from redis.asyncio import Redis
from src.bot.config import config


class RedisHelper:
    """Helper для работы с Redis"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.prefix = config.redis_key_prefix
    
    def _make_key(self, namespace: str, tg_id: int, extra: Optional[str] = None) -> str:
        """Создание ключа Redis"""
        key = f"{self.prefix}{namespace}:{tg_id}"
        if extra:
            key += f":{extra}"
        return key
    
    # Навигация и страницы
    async def set_page(self, tg_id: int, page_type: str, page: int) -> None:
        """Сохранить номер страницы для пользователя"""
        key = self._make_key("page", tg_id, page_type)
        await self.redis.set(key, page)
    
    async def get_page(self, tg_id: int, page_type: str, default: int = 1) -> int:
        """Получить номер страницы для пользователя"""
        key = self._make_key("page", tg_id, page_type)
        value = await self.redis.get(key)
        return int(value) if value else default
    
    async def clear_pages(self, tg_id: int) -> None:
        """Очистить все страницы пользователя"""
        pattern = f"{self.prefix}page:{tg_id}:*"
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
    
    # Контекст платежей
    async def set_payment_context(
        self, 
        payment_id: str, 
        tg_id: int, 
        subscription_id: int,
        message_id: int
    ) -> None:
        """Сохранить контекст платежа"""
        data = {
            "tg_id": tg_id,
            "subscription_id": subscription_id,
            "message_id": message_id
        }
        key = self._make_key("payment", payment_id, "context")
        await self.redis.setex(key, 86400, json.dumps(data))  # TTL 24 часа
    
    async def get_payment_context(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Получить контекст платежа"""
        key = self._make_key("payment", payment_id, "context")
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def update_payment_message_id(self, payment_id: str, message_id: int) -> None:
        """Обновить ID сообщения для платежа"""
        context = await self.get_payment_context(payment_id)
        if context:
            context["message_id"] = message_id
            key = self._make_key("payment", payment_id, "context")
            await self.redis.setex(key, 86400, json.dumps(context))
    
    async def clear_payment_context(self, payment_id: str) -> None:
        """Очистить контекст платежа"""
        key = self._make_key("payment", payment_id, "context")
        await self.redis.delete(key)
    
    # Черновики рассылок
    async def set_broadcast_draft(
        self, 
        admin_tg_id: int, 
        text: str, 
        segment: Optional[str] = None
    ) -> None:
        """Сохранить черновик рассылки"""
        data = {"text": text}
        if segment:
            data["segment"] = segment
        
        key = self._make_key("broadcast", admin_tg_id, "draft")
        await self.redis.setex(key, 3600, json.dumps(data))  # TTL 1 час
    
    async def get_broadcast_draft(self, admin_tg_id: int) -> Optional[Dict[str, Any]]:
        """Получить черновик рассылки"""
        key = self._make_key("broadcast", admin_tg_id, "draft")
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def clear_broadcast_draft(self, admin_tg_id: int) -> None:
        """Очистить черновик рассылки"""
        key = self._make_key("broadcast", admin_tg_id, "draft")
        await self.redis.delete(key)
    
    # Контекст уведомлений
    async def set_notification_context(
        self, 
        tg_id: int, 
        subscription_id: int,
        context_type: str = "renew"
    ) -> None:
        """Сохранить контекст уведомления"""
        key = self._make_key("notification", tg_id, context_type)
        await self.redis.setex(key, 3600, subscription_id)  # TTL 1 час
    
    async def get_notification_context(
        self, 
        tg_id: int, 
        context_type: str = "renew"
    ) -> Optional[int]:
        """Получить контекст уведомления"""
        key = self._make_key("notification", tg_id, context_type)
        value = await self.redis.get(key)
        return int(value) if value else None
    
    async def clear_notification_context(
        self, 
        tg_id: int, 
        context_type: str = "renew"
    ) -> None:
        """Очистить контекст уведомления"""
        key = self._make_key("notification", tg_id, context_type)
        await self.redis.delete(key)
    
    # Язык пользователя (кеш)
    async def set_user_language(self, tg_id: int, language: str) -> None:
        """Сохранить язык пользователя в кеше"""
        key = self._make_key("user", tg_id, "language")
        await self.redis.setex(key, 86400, language)  # TTL 24 часа
    
    async def get_user_language(self, tg_id: int) -> Optional[str]:
        """Получить язык пользователя из кеша"""
        key = self._make_key("user", tg_id, "language")
        return await self.redis.get(key)
    
    # Очистка всех данных пользователя
    async def clear_user_data(self, tg_id: int) -> None:
        """Очистить все данные пользователя"""
        pattern = f"{self.prefix}*:{tg_id}:*"
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
        
        # Также очищаем ключи без extra
        pattern = f"{self.prefix}*:{tg_id}"
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
