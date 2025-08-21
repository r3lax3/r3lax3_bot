"""
HTTP клиент для Backend API
"""
import httpx
import asyncio
from typing import Dict, Any, Optional, List
from src.bot.config import config


class BackendAPIClient:
    """Клиент для работы с Backend API"""
    
    def __init__(self):
        self.base_url = config.backend_api_base_url.rstrip('/')
        self.token = config.backend_api_token
        self.timeout = httpx.Timeout(connect=2.0, read=5.0, write=5.0, pool=10.0)
        
        # Заголовки по умолчанию
        self.default_headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Выполнить HTTP запрос к API"""
        url = f"{self.base_url}{endpoint}"
        headers = self.default_headers.copy()
        
        if idempotency_key and config.idempotency_enabled:
            headers["X-Idempotency-Key"] = idempotency_key
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=headers
                )
                
                # Обработка ошибок
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        await asyncio.sleep(int(retry_after))
                    else:
                        await asyncio.sleep(0.5)
                    # Повторяем запрос (максимум 2 раза)
                    return await self._make_request(method, endpoint, data, params, idempotency_key)
                
                response.raise_for_status()
                
                if response.status_code == 204:  # No Content
                    return {}
                
                return response.json()
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 400:
                    raise ValueError(f"Bad request: {e.response.text}")
                elif e.response.status_code == 401:
                    raise ValueError("Unauthorized")
                elif e.response.status_code == 404:
                    raise ValueError("Not found")
                elif e.response.status_code == 429:
                    raise ValueError("Rate limit exceeded")
                else:
                    raise ValueError(f"HTTP error {e.response.status_code}: {e.response.text}")
            except httpx.RequestError as e:
                raise ValueError(f"Network error: {str(e)}")
    
    # Пользователи
    async def get_user(self, tg_id: int) -> Dict[str, Any]:
        """Получить пользователя"""
        return await self._make_request("GET", f"/users/{tg_id}")
    
    async def update_user_language(self, tg_id: int, language: str) -> None:
        """Обновить язык пользователя"""
        await self._make_request("POST", f"/users/{tg_id}/language", {"language": language})
    
    async def update_user(self, tg_id: int, **kwargs) -> None:
        """Обновить пользователя"""
        await self._make_request("PATCH", f"/users/{tg_id}", kwargs)
    
    # Подписки
    async def get_user_subscriptions(self, tg_id: int, page: int = 1) -> Dict[str, Any]:
        """Получить подписки пользователя"""
        return await self._make_request("GET", f"/users/{tg_id}/subscriptions", params={"page": page})
    
    async def get_subscription(self, subscription_id: int) -> Dict[str, Any]:
        """Получить подписку по ID"""
        return await self._make_request("GET", f"/subscriptions/{subscription_id}")
    
    # Сервисы
    async def get_service(self, service_id: int) -> Dict[str, Any]:
        """Получить сервис по ID"""
        return await self._make_request("GET", f"/services/{service_id}")
    
    async def get_service_payment_options(self, service_id: int) -> Dict[str, Any]:
        """Получить варианты оплаты для сервиса"""
        return await self._make_request("GET", f"/services/{service_id}/payment-options")
    
    # Платежи
    async def create_payment(
        self, 
        tg_id: int, 
        service_id: int, 
        plan: str, 
        provider: str,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Создать платеж"""
        data = {
            "tg_id": tg_id,
            "service_id": service_id,
            "plan": plan,
            "provider": provider
        }
        return await self._make_request("POST", "/payments", data, idempotency_key=idempotency_key)
    
    async def get_user_payments(self, tg_id: int, page: int = 1) -> Dict[str, Any]:
        """Получить платежи пользователя"""
        return await self._make_request("GET", f"/users/{tg_id}/payments", params={"page": page})
    
    async def get_payment(self, payment_id: str) -> Dict[str, Any]:
        """Получить платеж по ID"""
        return await self._make_request("GET", f"/payments/{payment_id}")
    
    # Админ функции
    async def search_users(self, query: str) -> List[Dict[str, Any]]:
        """Поиск пользователей"""
        response = await self._make_request("GET", "/admin/users/search", params={"q": query})
        return response.get("items", [])
    
    async def get_admin_user(self, tg_id: int) -> Dict[str, Any]:
        """Получить пользователя для админа"""
        return await self._make_request("GET", f"/admin/users/{tg_id}")
    
    async def extend_subscription(self, subscription_id: int, plan: str) -> None:
        """Продлить подписку (админ)"""
        await self._make_request("POST", f"/admin/subscriptions/{subscription_id}/extend", {"plan": plan})
    
    async def create_subscription(
        self, 
        tg_id: int, 
        service_id: int, 
        plan: str, 
        until_date: Optional[str] = None
    ) -> None:
        """Создать/изменить подписку (админ)"""
        data = {"tg_id": tg_id, "service_id": service_id, "plan": plan}
        if until_date:
            data["until_date"] = until_date
        await self._make_request("POST", "/admin/subscriptions", data)
    
    async def start_service(self, service_id: int) -> None:
        """Запустить сервис"""
        await self._make_request("POST", f"/admin/services/{service_id}/start")
    
    async def pause_service(self, service_id: int) -> None:
        """Остановить сервис"""
        await self._make_request("POST", f"/admin/services/{service_id}/pause")
    
    async def resume_service(self, service_id: int) -> None:
        """Возобновить сервис"""
        await self._make_request("POST", f"/admin/services/{service_id}/resume")
    
    async def get_broadcast_recipients(
        self, 
        segment: str, 
        cursor: Optional[str] = None,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """Получить получателей для рассылки"""
        params = {"segment": segment, "limit": limit}
        if cursor:
            params["cursor"] = cursor
        return await self._make_request("GET", "/admin/broadcast/recipients", params=params)
    
    # Телеметрия
    async def send_event(self, event_type: str, tg_id: int, payload: Optional[Dict[str, Any]] = None) -> None:
        """Отправить событие"""
        data = {
            "type": event_type,
            "tg_id": tg_id
        }
        if payload:
            data["payload"] = payload
        
        await self._make_request("POST", "/events", data)


# Глобальный экземпляр клиента
api_client = BackendAPIClient()
