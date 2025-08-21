# R3lax3 Bot - Telegram Frontend Bot

Telegram бот для управления подписками на услуги с интеграцией Backend API.

## Возможности

- Управление подписками (просмотр, продление)
- История платежей
- Поддержка RU/EN языков
- Интеграция с платежными провайдерами через Backend API
- Админ-панель для управления сервисами и рассылок

## Установка

1. Клонируйте репозиторий
2. Установите зависимости: `pip install -r requirements.txt`
3. Скопируйте `.env.example` в `.env` и настройте переменные
4. Запустите бота: `python -m src.bot.main`

## Тестирование

Для проверки работы основных модулей запустите:

```bash
python test_bot.py
```

Этот скрипт проверит:
- Работу переводов (RU/EN)
- Генерацию callback данных
- Загрузку конфигурации

## Конфигурация

Создайте файл `.env` со следующими переменными:

```env
BOT_TOKEN=your_telegram_bot_token
BACKEND_API_BASE_URL=http://localhost:8000
BACKEND_API_TOKEN=your_backend_api_token
SUPPORT_LINK=https://t.me/support
DEFAULT_LANGUAGE=ru
TIMEZONE=UTC
FSM_STORAGE_URL=redis://localhost:6379
ADMIN_USER_IDS=123456789
BOT_INTERNAL_WEBHOOK_TOKEN=your_internal_token
INTERNAL_SERVER_HOST=0.0.0.0
INTERNAL_SERVER_PORT=8080
REDIS_KEY_PREFIX=clubifybot:
TELEGRAM_DELIVERY_RPS=20
BROADCAST_BATCH_SIZE=1000
USE_LONG_POLLING=true
IDEMPOTENCY_ENABLED=true
```

## Структура проекта

```
src/
├── bot/           # Точка входа и конфигурация
├── routers/       # Роутеры для обработки команд
├── states/        # FSM состояния
├── keyboards/     # Клавиатуры и кнопки
├── i18n/          # Локализация
├── clients/       # HTTP клиент для Backend API
├── services/      # Бизнес-логика
├── storage/       # Redis helpers
└── utils/         # Утилиты
```
