#!/usr/bin/env python3
"""
Простой тест для проверки работы бота
"""
import asyncio
import os
from src.bot.config import config
from src.i18n.translations import translations
from src.keyboards.factories import SubscriptionCallback, PaymentCallback


async def test_translations():
    """Тест переводов"""
    print("=== Тест переводов ===")
    
    # Тест русских переводов
    ru_text = translations.get("menu.main.title", "ru")
    print(f"RU: {ru_text}")
    
    # Тест английских переводов
    en_text = translations.get("menu.main.title", "en")
    print(f"EN: {en_text}")
    
    # Тест с плейсхолдерами
    ru_with_placeholder = translations.get("subscriptions.detail.title", "ru", 
                                         service_name="Test Service", until_date="01.01.2025")
    print(f"RU with placeholder: {ru_with_placeholder}")


async def test_callback_factories():
    """Тест фабрик callback данных"""
    print("\n=== Тест callback фабрик ===")
    
    # Тест подписки
    sub_callback = SubscriptionCallback(action="detail", subscription_id=123)
    packed = sub_callback.pack()
    print(f"Subscription callback: {packed}")
    
    # Тест платежа
    pay_callback = PaymentCallback(action="check", payment_id="pay_123")
    packed = pay_callback.pack()
    print(f"Payment callback: {packed}")
    
    # Проверяем размер
    print(f"Subscription callback size: {len(packed)} bytes")
    print(f"Payment callback size: {len(packed)} bytes")


async def test_config():
    """Тест конфигурации"""
    print("\n=== Тест конфигурации ===")
    
    print(f"Default language: {config.default_language}")
    print(f"Redis prefix: {config.redis_key_prefix}")
    print(f"Admin users: {config.admin_user_ids}")
    print(f"Backend API URL: {config.backend_api_base_url}")


async def main():
    """Основная функция тестирования"""
    print("R3lax3 Bot - Тестирование")
    print("=" * 30)
    
    try:
        await test_translations()
        await test_callback_factories()
        await test_config()
        
        print("\n✅ Все тесты прошли успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Устанавливаем переменные окружения для тестирования
    os.environ.setdefault("BOT_TOKEN", "test_token")
    os.environ.setdefault("BACKEND_API_BASE_URL", "http://localhost:8000")
    os.environ.setdefault("BACKEND_API_TOKEN", "test_token")
    os.environ.setdefault("SUPPORT_LINK", "https://t.me/support")
    os.environ.setdefault("BOT_INTERNAL_WEBHOOK_TOKEN", "test_token")
    
    asyncio.run(main())
