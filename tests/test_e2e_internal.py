import asyncio
import json
import pytest
from aiohttp.test_utils import TestServer, TestClient
from aiohttp import web

from src.bot.internal_server import _build_app
from src.bot.config import config
from src.clients.backend_api import api_client


class FakeBot:
    def __init__(self):
        self.calls = []

    async def edit_message_text(self, chat_id, message_id, text, reply_markup=None):
        self.calls.append(("edit", chat_id, message_id, text))
        return None

    async def send_message(self, chat_id, text, reply_markup=None):
        self.calls.append(("send", chat_id, None, text))
        class Msg:
            def __init__(self, mid):
                self.message_id = mid
        return Msg(999)


class FakeRedisHelper:
    def __init__(self):
        self.ctx = {}

    async def get_payment_context(self, payment_id: str):
        return self.ctx.get(payment_id)

    async def update_payment_message_id(self, payment_id: str, message_id: int):
        if payment_id in self.ctx:
            self.ctx[payment_id]["message_id"] = message_id

    async def clear_payment_context(self, payment_id: str):
        self.ctx.pop(payment_id, None)


@pytest.mark.asyncio
async def test_internal_notify_paid(monkeypatch):
    fake_bot = FakeBot()
    fake_redis = FakeRedisHelper()
    # Предзаполняем контекст оплаты
    fake_redis.ctx["pay1"] = {"tg_id": 111, "subscription_id": 123, "message_id": 1}

    # Токен для уведомлений
    old_token = config.bot_internal_webhook_token
    config.bot_internal_webhook_token = "testtoken"

    # Мокаем Backend API ответы
    async def fake_make_request(method, endpoint, data=None, params=None, idempotency_key=None):
        if endpoint.startswith("/payments/"):
            return {"id": "pay1", "status": "paid", "expires_at": "2099-01-01T00:00:00Z"}
        if endpoint.startswith("/subscriptions/"):
            return {"id": 123, "service_id": 5, "service_name": "Demo", "status": "active", "until_date": "2025-01-01T00:00:00Z"}
        return {}

    monkeypatch.setattr(api_client, "_make_request", fake_make_request)

    app = _build_app(fake_bot, fake_redis)
    server = TestServer(app)
    await server.start_server()
    client = TestClient(server)
    await client.start_server()

    try:
        resp = await client.post(
            config.internal_webhook_path,
            headers={"X-Internal-Token": "testtoken"},
            json={"payment_id": "pay1", "status": "paid"},
        )
        assert resp.status == 200
        # Проверяем, что бот отрисовал успех
        assert any("Оплата получена" in call[3] for call in fake_bot.calls)
    finally:
        await client.close()
        await server.close()
        config.bot_internal_webhook_token = old_token

