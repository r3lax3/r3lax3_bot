## Техническое задание: Backend API для Telegram Frontend‑бота (MVP)

### 1. Цели и зона ответственности
- Обеспечить единый REST API для фронтенд‑бота (далее «бот») для управления пользователями, подписками, платежами, контентом (FAQ/поддержка), административными функциями и напоминаниями.
- Инкапсулировать логику платёжных провайдеров (YooKassa, PayPal, Cryptomus): создание счёта, получение вебхуков, смена статусов платежей, продление подписок.
- Производить сервисные уведомления в бот (внутренние HTTP‑вызовы) об изменении статусов платежей и о напоминаниях.
- Не хранить и не выдавать секреты бота; аутентификация между ботом и Backend — по сервисному Bearer‑токену.

Границы ответственности:
- Backend: бизнес‑логика, хранение данных, платежи, напоминания, расчёт продления и «заморозки» при паузе сервиса, выборки для рассылок.
- Бот: UI/UX, FSM, локализация, безопасные вызовы API, отображение статусов, отправка рассылок по списку получателей из Backend.

### 2. Архитектура и стек
- Язык/фреймворк: Python 3.11+, FastAPI 0.111+ (ASGI), Uvicorn.
- ORM/БД: SQLAlchemy 2.x + Alembic; PostgreSQL 15+.
- Кэш/очереди/лимиты: Redis 6+.
- HTTP‑клиент: httpx (async) с таймаутами и ретраями (идемпотентные запросы только).
- Планировщик: APScheduler (задания напоминаний T‑3/T‑1/T‑0 и обслуживающие задачи). Фоновых очередей Celery — нет в MVP.
- Контейнеризация: Docker image; конфигурация через ENV.

Нефункциональные требования:
- P95 ответа API ≤ 200 мс при нормальной нагрузке, P99 ≤ 500 мс.
- Идемпотентность `POST /payments` по заголовку `Idempotency-Key`.
- Логи структурированные JSON; корреляция по `request_id`, `tg_id`, `payment_id`.

### 3. Модель данных (упрощённо, имена полей — итоговые контракты)
- User: `id`, `tg_id` (unique), `username?`, `language` ("ru"|"en"), `used_bot_before` (bool), `created_at`.
- Service: `id`, `name`, `status` ("running"|"paused"|"stopped"|"error"), `support_link?`.
- Subscription: `id`, `user_id`, `service_id`, `status` ("active"|"expired"|"paused"), `until_date` (UTC), `paused_at?`, `remaining_frozen_seconds?`.
- Payment: `id` (string), `user_id`, `service_id`, `provider` ("yookassa"|"paypal"|"cryptomus"), `plan` ("m1"|"m3"|"m6"|"y1"), `amount`, `currency`, `external_id?`, `status` ("created"|"pending"|"paid"|"failed"|"canceled"|"refunded"|"chargeback"), `description?`, `created_at`, `updated_at`, `expires_at?`.

Индексы: по `tg_id`, `service_id`, `status`, `created_at`.

### 4. Аутентификация и безопасность
- Все вызовы бота к Backend: заголовок `Authorization: Bearer <BACKEND_API_TOKEN>`.
- Все внутренние вызовы Backend → бот: заголовок `X-Internal-Token: <BOT_INTERNAL_WEBHOOK_TOKEN>`.
- Только HTTPS (TLS) снаружи; для dev допускается HTTP.
- Rate limiting per `tg_id` и по IP: чтение 60 r/m, изменения 12 r/m (конфигурируемо).
- Rate limiting per `tg_id` и по IP: чтение 60 r/m, изменения 12 r/m (конфигурируемо). При 429 Backend возвращает заголовки: `Retry-After` (секунды до следующей попытки), `X-RateLimit-Remaining`, `X-RateLimit-Reset` (unix‑ts/ISO8601).
- Формат ошибок: `{ code: string, message: string, details?: object }`.

### 5. Контракты API (строгое соответствие фронтенду)

5.1 Users
- GET /users/{tg_id} → `{ tg_id: int, language: "ru"|"en", used_bot_before: bool }`
- PATCH /users/{tg_id} body `{ language?: "ru"|"en", used_bot_before?: bool }` → `204`
- POST /users/{tg_id}/language body `{ language: "ru"|"en" }` → `204`

5.2 Subscriptions
- GET /users/{tg_id}/subscriptions?page=1 → `{ items: [ { id: int, service_id: int, service_name: string, status: "active"|"expired"|"paused", until_date: string|null } ], page: int, pages: int }`
- GET /subscriptions/{id} → `{ id: int, service_id: int, service_name: string, status: string, until_date: string|null }`

5.3 Services
- GET /services/{id} → `{ id: int, name: string, status: "running"|"paused"|"stopped"|"error", support_link?: string }`
- GET /services/{service_id}/payment-options → `{ providers: ["yookassa"|"paypal"|"cryptomus"...], plans: [ { code: "m1"|"m3"|"m6"|"y1", amount: number, currency: string } ] }`
  - В одном ответе все `plans` имеют единую валюту. Иначе — 400 `validation_error`.
- GET /services/{id}/faq?lang=ru|en → `{ text: string }` (если нет — 404 `not_found`)

5.4 Payments
- POST /payments (Idempotency-Key обязателен)
  - body `{ tg_id: int, service_id: int, plan: "m1"|"m3"|"m6"|"y1", provider: string }`
  - → `{ payment_id: string, pay_link?: string, qr_url?: string, instructions?: string, expires_at: string }`
- GET /users/{tg_id}/payments?page=1 → `{ items: [ { id: string, provider: string, amount: number, currency: string, status: string, date: string, description?: string, external_id?: string } ], page: int, pages: int }`
- GET /payments/{id} → `{ id: string, provider: string, amount: number, currency: string, status: string, date: string, description?: string, external_id?: string }`

5.5 Admin (доступ по роли admin, проверка токена + RBAC)
- GET /admin/users/search?q=... → `[ { tg_id, username?, language, subscriptions_count } ]`
- GET /admin/users/{tg_id} → `{ profile: {...}, subscriptions: [...], last_payments: [...] }`
- POST /admin/subscriptions/{id}/extend body `{ plan: "m1"|"m3"|"m6"|"y1" }` → `200 { until_date }`
- POST /admin/subscriptions body `{ tg_id: int, service_id: int, plan: "m1"|"m3"|"m6"|"y1", until_date?: string }` → `201 { id, until_date }`
- POST /admin/services/{id}/start → `204`
- POST /admin/services/{id}/pause → `204`
- POST /admin/services/{id}/resume → `204`
- GET /admin/broadcast/recipients?segment=all|active_subs|no_active_subs|service:<id>&cursor=&limit=1000 → `{ items: number[], next_cursor?: string }`
- GET /admin/stats → `{ users_total, users_active, active_subscriptions, mrr: [ { currency: string, amount: number } ] }`

5.6 Вебхуки провайдеров → Backend
- POST /webhooks/yookassa | /webhooks/paypal | /webhooks/cryptomus
  - Проверка подписи/секрета провайдера; идемпотентность по `external_id`.
  - Обновление `Payment.status` и корреспондирующих сущностей.

### 6. Интеграция Backend → бот (исходящие вызовы)
- Изменение статуса платежа → `POST {BOT_BASE_URL}{INTERNAL_WEBHOOK_PATH}`
  - Заголовок: `X-Internal-Token`
  - Тело: `{ payment_id: string, status: "created"|"pending"|"paid"|"failed"|"canceled"|"refunded"|"chargeback" }`
- Напоминание о продлении → `POST {BOT_BASE_URL}/internal/notifications/renew`
  - Заголовок: `X-Internal-Token`
  - Тело: `{ tg_id: number, subscription_id: number }`

Повторы допускаются; бот обязан быть идемпотентен (см. фронтенд‑ТЗ).

### 7. Бизнес‑правила
7.1 Продление подписок
- Планы: `m1=1 мес`, `m3=3 мес`, `m6=6 мес`, `y1=12 мес`.
- Если подписка `active`: продление от текущего `until_date`.
- Если `expired` или отсутствует: `until_date = now_utc + duration`.
- При `service.status=paused`: оплаченные продления накапливаются в `remaining_frozen_seconds`; активация происходит при `resume` (см. ниже).

7.2 Пауза/возобновление сервиса
- `pause`: Backend фиксирует `paused_at` в сервисе и «замораживает» ход времени активных подписок: сохраняет `remaining_frozen_seconds = max(until_date - now, 0)` и ставит подписку в `paused`.
- `resume`: Backend для каждой `paused` подписки вычисляет `until_date = now + remaining_frozen_seconds`; обнуляет `remaining_frozen_seconds` и переводит подписку в `active`.

7.3 Статусы платежей
- Внутренние: `created`, `pending`, `paid`, `failed`, `canceled`, `refunded`, `chargeback`.
- Переходы:
  - `created|pending → paid|failed|canceled` (по вебхуку/проверке провайдера)
  - `paid → refunded|chargeback`
  - Повторные вебхуки с тем же статусовым событием — игнорируются (идемпотентность).

7.4 Идемпотентность `POST /payments`
- Требуется заголовок `Idempotency-Key` (UUIDv4). Backend хранит ключ и ответ на 24 ч; повтор возвращает тот же `payment_id` и атрибуты.
- Должен проверяться «активный счёт на подписку»: при наличии незавершённого платежа по `tg_id+service_id` возвращается 409 `conflict` с актуальным `payment_id` в `details`.

7.5 Пагинация
- Фиксированный размер страницы: 10 элементов. Поля `page` (1‑based), `pages` ≥ 1. Выход за диапазон → пустой список и корректный `pages`.

### 8. Провайдеры платежей (MVP)
- YooKassa: redirect confirmation; возвращаем `pay_link`.
- PayPal: Orders API; возвращаем approve `pay_link`.
- Cryptomus: оплата через внешнюю инвойс‑страницу провайдера; Backend возвращает `pay_link` на эту страницу. `qr_url` может отсутствовать и никогда не генерируется на Backend; если провайдер вернёт прямую ссылку на QR‑изображение, она может быть передана как опциональное поле. Основной UX на фронте — открытие `pay_link`.

Общее:
- Все интеграции через httpx с таймаутами; хранить `external_id` и минимум метаданных.
- Вебхуки провайдеров валидируются и приводятся к единому виду (см. 7.3).

### 9. Ошибки и коды
- 400 `validation_error`, 401 `unauthorized`, 403 `forbidden`, 404 `not_found`, 409 `conflict|idempotency_conflict`, 429 `rate_limited`, 500 `internal_error`, 503 `provider_unavailable`.
- Тело ошибки: `{ code, message, details? }`.

#### 9.1. Пример 429 (rate limited)
Заголовки:
```
Retry-After: 2
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 2025-01-01T12:00:02Z
X-Request-Id: 5f0c0e1a-...
```
Тело:
```
{ "code": "rate_limited", "message": "Too many requests", "details": { "scope": "tg_id", "window": "60s" } }
```

### 10. Наблюдаемость
- Логи JSON с уровнями INFO/ERROR; ключи корреляции: `request_id`, `tg_id`, `payment_id`.
- Метрики (при наличии): количество платежей по статусам, время ответа вебхуков, количество напоминаний.
- Ретеншн логов: 30 дней. Конвенции корреляции:
  - Каждый входящий запрос получает `request_id` (UUID); эхо в ответе и логах.
  - Бот может передавать `X-Request-Id` — Backend примет его как `request_id` и вернёт тем же заголовком в ответе.
  - Для платежных операций в логах всегда указываются `payment_id` и `tg_id`.

### 11. Конфигурация (ENV)
- `DATABASE_URL` (PostgreSQL)
- `REDIS_URL`
- `BACKEND_API_TOKEN` (проверка бота)
- `BOT_BASE_URL` (для внутренних вызовов в бот)
- `BOT_INTERNAL_WEBHOOK_TOKEN` (секрет для вызовов в бот)
- `HTTP_TIMEOUTS` (CONNECT=2s, READ=5s, WRITE=5s, POOL=10s)
- Провайдеры: `YKS_*`, `PAYPAL_*`, `CRYPTOMUS_*` (ключи, секреты, вебхук‑секреты)
- `TIMEZONE=UTC`

### 12. Тестирование
- Юнит‑тесты: расчёт продления/паузы, идемпотентность платежей, маппинг статусов, валидация контрактов.
- Интеграционные: флоу «создать платёж → вебхук paid → продление подписки → уведомление бота» по каждому провайдеру (моки).
- Регрессии: истёкший счёт, повторный вебхук, конфликт активного счёта, отсутствие FAQ.

### 13. Соглашения о датах/деньгах
- Все даты в ISO8601 UTC (`YYYY-MM-DDTHH:MM:SSZ`).
- Денежные суммы — `number` с двумя знаками после запятой для RUB/USD/EUR; валюта — ISO‑код.

### 14. Примеры

14.1 GET /users/{tg_id}
```
{
  "tg_id": 123456789,
  "language": "ru",
  "used_bot_before": true
}
```

14.2 POST /payments (Idempotency-Key: 0f0b2...)
```
{
  "tg_id": 123456789,
  "service_id": 42,
  "plan": "m1",
  "provider": "yookassa"
}
```
→
```
{
  "payment_id": "pay_abc123",
  "pay_link": "https://...",
  "expires_at": "2025-01-01T12:00:00Z"
}
```

14.3 Вебхук провайдера → уведомление бота
```
POST {BOT_BASE_URL}/internal/payments/notify
Headers: X-Internal-Token: ***
Body: { "payment_id": "pay_abc123", "status": "paid" }
```

---

Этот документ является источником истины для реализации Backend в рамках MVP и полностью согласован с `docs/TZ.FrontendBot.md`.

## Техническое задание: Backend API и оркестрация проектов (MVP)

### 1. Цели
- Предоставить единый Backend API для фронтенд‑бота: пользователи, подписки, платежи, уведомления, тексты (FAQ, оферта), конфигурации проектов.
- Инкапсулировать логику платёжных провайдеров (ЮKassa, PayPal, Cryptomus), управлять рекуррентными платежами, статусовыми вебхуками.
- Обеспечить управление жизненным циклом «проектов» (ботов‑клиентов): создание, деплой/запуск/остановка/перезапуск без ручного захода на сервер и настройки Nginx/systemd.

### 2. Архитектура
- Компоненты:
  - REST API (FastAPI) + async ORM (SQLAlchemy/SQLModel) + Celery/RQ/Apscheduler для фоновых задач.
  - Платёжные адаптеры: Yookassa, PayPal, Cryptomus. Единый интерфейс.
  - Менеджер проектов: управление деплоем и состоянием ботов. Для MVP: Docker‑оркестрация (Docker Engine API + templates). Позже: Kubernetes.
  - Хранилище: PostgreSQL.
  - Кэш: Redis (сессии, rate limits, очереди).
  - Файлы (оферта/FAQ‑ресурсы): S3‑совместимое хранилище (MinIO/S3), CDN‑линки.

### 3. Модель данных (упрощённо)
- User
  - id (int, pk), tg_id (bigint, unique), username, language (ru|en), used_bot_before (bool), created_at
- Service (aka Project)
  - id, name, description, owner_id (fk User), status (running|paused|stopped|error), is_active (bool)
  - pricing_plans: JSON [{code: m1|m3|m6|y1, amount, currency}]
  - providers: JSON {yookassa: {enabled, recurring_enabled}, paypal: {...}, cryptomus: {...}}
  - offer_pdf_url, faq_text_ru, faq_text_en, support_link
  - bot_metadata: JSON {bot_token, webhook_url?, env_overrides}
- Subscription
  - id, user_id, service_id, status (active|grace|expired|paused), ends_at (date), started_at
- Payment
  - id, user_id, service_id, provider (yookassa|paypal|cryptomus), plan_code (m1|m3|m6|y1)
  - amount, currency, external_id, status (created|pending|paid|failed|canceled|refunded|chargeback)
  - created_at, processed_at, metadata JSON (ip, ua, description)
- AuditLog
  - id, actor_id, action, entity_type, entity_id, payload, created_at

Все модели с индексами по часто фильтруемым полям: user_id, service_id, status, created_at.

### 4. Контракты API (основные)
- Аутентификация: Bearer token (сервисный токен для бота), админские JWT для панели админа (в боте/внешней панели).

- Users
  - GET /users/{tg_id}
  - PATCH /users/{tg_id} {language?, used_bot_before?}
  - POST /users/{tg_id}/language {language}

- Subscriptions
  - GET /users/{tg_id}/subscriptions?page
  - GET /subscriptions/{id}
  - POST /subscriptions/{id}/gift {plan_code}
  - POST /subscriptions/{id}/pause
  - POST /subscriptions/{id}/resume

- Services (Projects)
  - GET /services
  - GET /services/{id}
  - GET /services/{id}/payment-options → {providers[], plans[]}
  - GET /services/{id}/faq → {text}
  - GET /services/{id}/offer → {url}

- Payments
  - POST /payments {tg_id, service_id, plan_code, provider} (c заголовком Idempotency-Key)
  - GET /payments/{id}
  - GET /users/{tg_id}/payments?page
  - POST /payments/{id}/refund

- Events
  - POST /events {type, tg_id, payload?, ts?}

- Webhooks (external → API)
  - POST /webhooks/yookassa
  - POST /webhooks/paypal
  - POST /webhooks/cryptomus
  - Проверка подписи/секретов, идемпотентность.

- Admin
  - POST /admin/broadcast {segment, text}
  - GET /admin/broadcast/recipients?segment=all|active_subs|no_active_subs|service:<id>&cursor=&limit=1000
  - GET /admin/stats {range}
  - GET /admin/users?query
  - GET /admin/users/{id}
  - POST /admin/users/{id}/grant {plan_code, service_id}
  - POST /admin/payments/{id}/refund
  - Projects lifecycle:
    - POST /admin/projects {name, config}
    - POST /admin/projects/{id}/start
    - POST /admin/projects/{id}/stop
    - POST /admin/projects/{id}/restart
    - GET /admin/projects/{id}/status
    - POST /admin/projects/{id}/update-config {config}

### 5. Бизнес‑логика платежей
- Поддержка 3 провайдеров: Yookassa, PayPal, Cryptomus.
- Для каждого сервиса хранится флаг включённости провайдера и флаг доступности рекуррентных платежей.
- При создании платежа:
  1) Проверить, что провайдер включен для сервиса.
  2) Подготовить инвойс/ссылку с метаданными (tg_id, service_id, plan_code, идемпотентный ключ).
  3) Сохранить Payment со статусом `created`/`pending`.
  4) Вернуть фронту ссылку/QR/инструкции + срок действия.
- При получении вебхука провайдера:
  - Валидировать подпись.
  - Найти Payment по external_id.
  - Обновить статус: paid/failed/canceled/refunded/chargeback.
  - Если `paid` — продлить подписку: ends_at += план (1/3/6/12 мес), статус `active`.
  - Идемпотентность: повторные вебхуки игнорируются.
- Рекуррентные платежи:
  - Если провайдер и сервис разрешают рекуррентные платежи, при оплате картой сохраняем subscription/contract id.
  - Планировщик перед окончанием подписки инициирует автосписание. При успехе — продление. При неуспехе — уведомления и переход в grace.

#### 5.1. Провайдеры — детали
- YooKassa
  - Создание платежа: `POST /payments` → вызов API YooKassa `payments.create` с `idempotence-key`, `amount`, `currency`, `capture=true`, `description`, `metadata{user_id,service_id,plan_code}` и `confirmation{type: redirect, return_url}`.
  - Ответ хранит `payment.id` (external_id) и `confirmation_url` (pay_link).
  - Вебхук: проверка подписи, событие `payment.succeeded|canceled|waiting_for_capture` (если enabled), обрабатываем `succeeded` как paid.
  - Рекуррентные: первый платёж с `save_payment_method=true`, сохраняем `payment_method.id`/`customer_id`, последующие — `payments.create` с `payment_method_id` без участия пользователя. Требует включения в кабинете и модерации.

- PayPal
  - Одноразовый платёж: Orders API. Шаги: `orders.create` → возвращаем approve link → после callback фронт или воркер вызывает `orders.capture` (или ждём вебхук `PAYMENT.CAPTURE.COMPLETED`).
  - Вебхук: `CHECKOUT.ORDER.APPROVED`, `PAYMENT.CAPTURE.COMPLETED` — по capture считаем paid.
  - Рекуррентные: Subscriptions API (Billing Plans + Products). Для MVP возможно только одноразовые; для рекуррентных — предварительная верификация бизнеса и настройка планов на стороне PayPal.

- Cryptomus
  - Создание инвойса: `create invoice` с суммой и валютой, получаем `pay_url` и, при необходимости, `qr_code` (base64 или url). Храним `external_id`.
  - Вебхук: подпись (HMAC), событие `paid|failed|expired`. При `paid` — продление подписки.
  - Рекуррентные: нативного рекуррента может не быть. Для MVP только одноразовые; автосписание заменить напоминаниями.

Примечание: точные названия полей и маршрутов провайдеров будут уточнены по их актуальной документации на этапе реализации. В ТЗ зафиксированы протокольные шаги и требования к состояниям/вебхукам.

#### 5.2. Логика продления подписки
- Базовая единица планов: m1=1 месяц, m3=3 месяца, m6=6 месяцев, y1=12 месяцев.
- Если подписка `active` или `grace`: продлеваем от текущего `ends_at` (не от now), чтобы не терялось оставшееся время.
- Если подписка `expired` или отсутствует: устанавливаем `started_at=now`, `ends_at = now + duration`.
- При повторной оплате, пока предыдущая не обработана, использовать идемпотентность: один и тот же `Idempotency-Key` не создаёт дубликаты.
- Refund: перевод платежа в `refunded`, подписка откатывается на соответствующий период, если возможно; в MVP частичный возврат и пропорциональные перерасчёты не поддерживаются (только полный возврат последнего периода).

### 6. Напоминания и уведомления
- Планировщик задач (Celery beat/APScheduler):
  - T‑3, T‑1, T‑0 — инициировать уведомление в Frontend‑бот через внутренний HTTP бота (`POST /internal/notifications/renew`, заголовок `X-Internal-Token`).
  - Изменение статусов платежей — по вебхукам провайдеров → обновление состояния и push в Frontend‑бот (`POST /internal/payments/notify`, заголовок `X-Internal-Token`).
  - Grace‑period проверки.

### 7. Управление проектами (оркестрация)
- MVP стратегия: Docker‑оркестрация на одном/нескольких хостах.
- Компоненты:
  - Шаблон Docker image для клиентского бота (единый образ) с параметризацией ENV.
  - Шаблон docker-compose или контейнер через Docker Engine API.
  - Reverse‑proxy (Traefik/Caddy) автоконфигурируется через labels (без ручного Nginx). Для polling‑ботов достаточно outbound; для webhook‑ботов — маршрутизация вебхуков.
- API действия:
  - Создать проект: генерирует конфиг (env), создаёт запись Service, подготавливает секреты, деплоит контейнер (или ставит в очередь деплоя).
  - Старт/стоп/рестарт: вызовы к Docker Engine API (или агенты на хостах), хранение статуса.
  - Обновить конфигурацию: перезапуск контейнера с новыми ENV.
  - Статус: сбор метрик контейнера (uptime, restarts, last logs excerpt).

#### 7.1. Workflow добавления проекта без ручных действий на сервере
1) Админ вызывает `POST /admin/projects` с: названием, описанием, owner_id, pricing_plans, providers config, bot_token, опциями (polling/webhook), ссылками на FAQ/оферту.
2) API валидирует бот‑токен (запрос к getMe), проверяет доступность чата уведомлений (опционально).
3) Создаёт секреты (Docker secrets), формирует ENV и labels для reverse‑proxy (если нужен webhook).
4) Запускает контейнер через Docker Engine API с привязкой к проектному network и volume (логи/данные, если нужно).
5) Пишет статус `running` при успешном health‑check (бот отвечает на /healthz через внутренний HTTP или через Bot API ping).
6) Возвращает детальную карточку проекта. Вся логика без SSH/Nginx/systemd, управляется API.

#### 7.2. Биллинг владельца проекта и «спящий режим»
- Для каждого `Service` требуется валидная подписка владельца (`owner_id`) на платформу. Модель: отдельная подписка уровня владельца либо специальный `Service` типа `platform`.
- Планировщик ежедневно проверяет статус: если у владельца статус `expired` (после grace), проект переводится в `paused` и контейнер останавливается.
- При возобновлении оплаты владельцем — API инициирует перезапуск контейнера и статус `running`.
- В это время Frontend‑бот остаётся доступен для владельца для оплаты и управления, а клиентский бот (проект) не обрабатывает апдейты (контейнер остановлен или webhook отключён).

### 8. Безопасность
- Хранение секретов в Secrets Manager (Docker Swarm/K8s secrets/Hashicorp Vault) — не в БД открытым текстом.
- Все внешние вызовы — по HTTPS. Вебхуки с проверкой подписи и IP‑allowlist (если доступно).
- Идемпотентные ключи для всех операций создания платежей.
- Роли: admin, support, owner. Разграничение доступа на уровне эндпоинтов.

### 8.1. Ошибки и коды ответа API
- Формат ошибок: `{code:string, message:string, details?:object}`.
- Общие коды:
  - `validation_error` (400)
  - `not_found` (404)
  - `forbidden` (403)
  - `unauthorized` (401)
  - `conflict` (409)
  - `rate_limited` (429)
  - `provider_unavailable` (503)
  - `idempotency_conflict` (409)
  - `orchestration_error` (502)

### 8.2. Rate limiting и идемпотентность
- Для `POST /payments` обязательный заголовок `Idempotency-Key` (генерируется фронтом или API, второй вариант — по умолчанию).
- Rate limits per tg_id: по умолчанию 30 r/m на чтение, 6 r/m на изменения.

### 9. Масштабирование
- Горизонтальное масштабирование API (N replicas), отдельные воркеры для задач.
- Кэширование справочников и конфигураций на 60–300 сек.
- Rate limiting per tg_id и per IP.

### 10. Тестирование
- Юнит‑тесты: платежные адаптеры (моки), расчёт продления, вебхуки, идемпотентность.
- Интеграционные: полный флоу платежа для каждого провайдера.
- E2E: мок‑бот вызывает API (через тестовый токен), проверка продления подписки.

### 11. Набор эндпоинтов — детализация схем

Пример схем (pydantic‑модели):
- PaymentCreateRequest: {user_id:int, service_id:int, plan_code:str, provider:str}
- PaymentCreateRequest: {tg_id:int, service_id:int, plan_code:str, provider:str}
- PaymentCreateResponse: {payment_id:int, provider:str, pay_link:str|null, qr_url:str|null, instructions:str|null, expires_at:str}
- PaymentDTO: {id, provider, amount, currency, status, external_id, description, created_at, processed_at}
- SubscriptionDTO: {id, service_id, service_name, status, ends_at}
- ServicePaymentOptions: {providers:[{code, enabled, recurring}], plans:[{code, amount, currency}]}

### 11.1. Примеры ответов
- GET /services/{id}/payment-options
```
{
  "providers": [
    {"code": "yookassa", "enabled": true, "recurring": true},
    {"code": "paypal", "enabled": true, "recurring": false},
    {"code": "cryptomus", "enabled": true, "recurring": false}
  ],
  "plans": [
    {"code": "m1", "amount": 10.0, "currency": "USD"},
    {"code": "m6", "amount": 50.0, "currency": "USD"},
    {"code": "y1", "amount": 90.0, "currency": "USD"}
  ]
}
```

### 11.2. Сегментация рассылок
- Поля сегмента: `all`, `active_subs`, `no_active_subs`, `service:<id>`.
- Поведение: предпросмотр → подтверждение → API отдаёт получателей батчами через `GET /admin/broadcast/recipients` (по `cursor`, `limit`), фронт‑бот отправляет с лимитом RPS и backoff; трекинг delivered/failed, повторная попытка на failed до 3 раз.


### 12. Журналы и аудит
- Логировать: создание платежей, переходы статусов, ошибки провайдеров, админ‑действия над проектами и пользователями.
- AuditLog доступен админам: фильтр по периоду, типу действий.

### 13. Миграции
- Alembic миграции. Начальный скрипт создаёт все таблицы, индексы, ограничения.

### 14. Развёртывание
- Prod: Docker images, Compose/Swarm/K8s. Один образ для Backend API, один — для клиентских ботов.
- Настройки через ENV и секреты. Авто‑миграции при старте.

### 15. SLA и мониторинг
- Health‑checks /healthz, readiness /readyz.
- Метрики Prometheus: RPS, latency, errors, payments status counts, webhook latency.
- Логи в stdout + централизованный сбор (ELK/Loki).

### 16. Правовые материалы
- Хранение и отдача оферты (PDF) через S3, версияция. Ссылки отдаются с ограниченным публичным доступом.

### 17. Локализация контента
- FAQ и оферта — per‑service поля, могут обновляться администратором; API вернёт соответствующую локаль.


