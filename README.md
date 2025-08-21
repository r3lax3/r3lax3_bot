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

### Pytest тесты

Установите зависимости и запустите:

```bash
pytest -q
```

Покрыто:
- i18n снапшоты ключей и плейсхолдеров
- Валидация сегментов и пагинации
- Ретраи GET запросов клиента

### E2E (минимум)

Рекомендуемый сценарий e2e:
1. Запустить локально Backend API (mock/реальный)
2. Установить `.env` и запустить бота `python -m src.bot.main`
3. Через Telegram протестировать: `/start`, список подписок, продление (создание счёта), историю платежей
4. Для push-уведомления оплаты вызвать HTTP:
   `POST http://<host>:8080/internal/payments/notify` с заголовком `X-Internal-Token` и телом `{ "payment_id": "...", "status": "paid" }`
5. Проверить обновление UI и возврат в карточку подписки

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

## Деплой

### Вариант 1: Docker Compose (рекомендуется)

1) Заполните `.env` (см. `env.example`).
2) Соберите и запустите:

```bash
docker compose up -d --build
```

Состав:
- `redis`: хранилище FSM
- `bot`: сам бот (long polling) и встроенный HTTP‑сервер для внутренних уведомлений

Порты:
- Внутренний сервер слушает `INTERNAL_SERVER_HOST:INTERNAL_SERVER_PORT` (см. .env). При необходимости пробросьте порт на хост.

Логи:
```bash
docker compose logs -f bot
```

### Вариант 2: Bare metal (systemd)

Требования: Python 3.11+, Redis. Установите зависимости и запустите как сервис.

1) Установка зависимостей:
```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

2) Настройте `.env`.

3) Юнит‑запуск:
```bash
python -m src.bot.main
```

4) Пример unit-файла systemd `/etc/systemd/system/r3lax3-bot.service`:
```
[Unit]
Description=R3lax3 Frontend Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/r3lax3_bot
EnvironmentFile=/opt/r3lax3_bot/.env
ExecStart=/opt/r3lax3_bot/.venv/bin/python -m src.bot.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now r3lax3-bot
sudo journalctl -u r3lax3-bot -f
```
