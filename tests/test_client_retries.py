import asyncio
import types
import httpx
import pytest
from src.clients.backend_api import BackendAPIClient


class DummyTransport(httpx.BaseTransport):
    def __init__(self):
        self.calls = 0
    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        # Первые два вызова 429, затем 200 JSON
        if self.calls <= 2:
            return httpx.Response(429, headers={"Retry-After": "0.0"})
        return httpx.Response(200, json={"ok": True})


@pytest.mark.asyncio
async def test_get_retries(monkeypatch):
    client = BackendAPIClient()
    # Подменяем AsyncClient, чтобы использовать DummyTransport
    async def fake_async_client(*args, **kwargs):
        transport = DummyTransport()
        return httpx.AsyncClient(transport=transport)
    # monkeypatch не подходит напрямую, заменим создание клиента контекстным менеджером
    orig_async_client = httpx.AsyncClient
    try:
        httpx.AsyncClient = lambda *a, **k: orig_async_client(transport=DummyTransport())
        res = await client._make_request("GET", "/health")
        assert "ok" in res
    finally:
        httpx.AsyncClient = orig_async_client
