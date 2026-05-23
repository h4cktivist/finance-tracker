# Finance Tracker — Backend

Production-ready backend на FastAPI для учёта личных финансов и бюджета.

## Стек

- Python 3.13+, FastAPI, PostgreSQL, SQLAlchemy 2 (async), Alembic, Redis, Celery
- JWT-аутентификация с ротацией refresh-токенов
- Двойная запись (ledger) для расчёта балансов счетов
- Кэшбэк, бюджеты, повторяющиеся операции, цели, аналитика, in-app уведомления

## Быстрый старт

```bash
cp .env.example .env
docker compose up -d postgres redis
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
```

В Docker миграции применяются автоматически сервисом `migrate` до старта `api`.

Документация API: http://localhost:8000/docs

## Docker (полный стек)

```bash
cp .env.example .env
docker compose up --build
```

При запуске сначала выполняется `alembic upgrade head` (сервис `migrate`), затем стартуют `api` и Celery.

Только миграции вручную:

```bash
docker compose run --rm migrate
```

Сервисы: `api` (порт 8000), `postgres`, `redis`, `celery-worker`, `celery-beat`

## API

Базовый URL: `http://localhost:8000`

Интерактивная документация: [/docs](http://localhost:8000/docs)

### Формат ответа

Успех:

```json
{
  "success": true,
  "data": {},
  "message": ""
}
```

Ошибка:

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Ресурс не найден",
    "details": {}
  }
}
```

### Аутентификация

Для всех эндпоинтов, кроме `/auth/*` и `/health`, передавайте заголовок:

```http
Authorization: Bearer <access_token>
```

Токены выдаются при `POST /api/v1/auth/login` или `POST /api/v1/auth/refresh`.

---

### Проверка здоровья (Health)

| Метод | Путь | Auth | Описание |
|-------|------|------|----------|
| GET | `/health` | нет | Проверка работоспособности |

**Ответ `data`:** `{ "status": "ok" }`

---

### Аутентификация — `/api/v1/auth`

На всех маршрутах действует rate limit (по умолчанию `10/minute`).

| Метод | Путь | Auth | Описание |
|-------|------|------|----------|
| POST | `/register` | нет | Регистрация |
| POST | `/login` | нет | Вход, выдача токенов |
| POST | `/refresh` | нет | Обновление access-токена |
| POST | `/logout` | нет | Отзыв refresh-токена |
| POST | `/reset-password` | нет | Запрос сброса или смена пароля |

#### POST `/register`

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `email` | string (email) | да | Email пользователя |
| `password` | string | да | Пароль, 8–128 символов |

#### POST `/login`

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `email` | string (email) | да | Email |
| `password` | string | да | Пароль |

**Ответ `data`:** `access_token`, `refresh_token`, `token_type` (`"bearer"`)

#### POST `/refresh` и POST `/logout`

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `refresh_token` | string | да | Refresh-токен из ответа login |

#### POST `/reset-password`

**Запрос токена** — только email:

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `email` | string (email) | да | Email |

При `DEBUG=true` в `message` может вернуться dev-токен.

**Смена пароля** — все три поля:

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `email` | string (email) | да | Email |
| `new_password` | string | да | Новый пароль, 8–128 символов |
| `reset_token` | string | да | Токен из Redis (email / dev) |

---

### Счета — `/api/v1/accounts`

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/` | Создать счёт |
| GET | `/` | Список счетов с балансами |
| GET | `/{account_id}` | Один счёт |
| PATCH | `/{account_id}` | Обновить метаданные |
| DELETE | `/{account_id}` | Мягкое удаление (soft delete) |

Баланс считается из `ledger_entries` + `initial_balance`.

#### POST `/` — тело запроса

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `name` | string | да | Название (макс. 255) |
| `type` | enum | да | `debit`, `credit`, `cash`, `savings` |
| `initial_balance` | decimal | нет | Стартовый баланс, ≥ 0, по умолчанию `0` |

#### PATCH `/{account_id}` — тело запроса

Все поля опциональны:

| Поле | Тип | Описание |
|------|-----|----------|
| `name` | string | Название |
| `type` | enum | `debit`, `credit`, `cash`, `savings` |

---

### Категории — `/api/v1/categories`

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/` | Создать категорию |
| GET | `/` | Плоский список |
| GET | `/tree` | Дерево (вложенные `children`) |
| PATCH | `/{category_id}` | Обновить |
| DELETE | `/{category_id}` | Мягкое удаление |

#### POST `/` — тело запроса

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `name` | string | да | Название |
| `type` | enum | да | `expense` (расход) или `income` (доход) |
| `parent_category_id` | UUID string | нет | Родительская категория; `null` = корневая |
| `color` | string | нет | Цвет (макс. 20) |
| `icon` | string | нет | Иконка (макс. 50) |
| `is_essential` | boolean | нет | Обязательный расход для аналитики, по умолчанию `true` |

Тип дочерней категории должен совпадать с типом родителя.

#### PATCH `/{category_id}`

| Поле | Тип | Описание |
|------|-----|----------|
| `name` | string | Название |
| `color` | string | Цвет |
| `icon` | string | Иконка |
| `is_essential` | boolean | Флаг обязательного расхода |
| `parent_category_id` | UUID string | Новый родитель |

---

### Теги — `/api/v1/tags`

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/` | Создать тег |
| GET | `/` | Список тегов |
| PATCH | `/{tag_id}` | Обновить |
| DELETE | `/{tag_id}` | Мягкое удаление |

#### POST `/`

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `name` | string | да | Уникально в рамках пользователя (макс. 100) |
| `color` | string | нет | Цвет |

#### PATCH `/{tag_id}`

| Поле | Тип | Описание |
|------|-----|----------|
| `name` | string | Название |
| `color` | string | Цвет |

---

### Транзакции — `/api/v1/transactions`

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/` | Создать транзакцию (или пару при переводе) |
| GET | `/` | Список с фильтрами и пагинацией |
| GET | `/{transaction_id}` | Одна транзакция |
| PATCH | `/{transaction_id}` | Обновить описание и теги (без суммы и счёта) |
| DELETE | `/{transaction_id}` | Мягкое удаление |
| POST | `/{transaction_id}/correct` | Исправление через новую транзакцию |

Сумму и счёт можно изменить только через `correct`, не через PATCH.

#### POST `/` — тело запроса

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `account_id` | UUID string | да | Счёт |
| `type` | enum | да | `expense`, `income`, `transfer` |
| `amount` | decimal | да | Сумма, > 0 |
| `transaction_date` | date (`YYYY-MM-DD`) | да | Дата операции |
| `category_id` | UUID string | нет | Категория |
| `description` | string | нет | Описание |
| `merchant_name` | string | нет | Магазин / получатель |
| `notes` | string | нет | Заметки |
| `tag_ids` | UUID[] | нет | Список ID тегов |
| `target_account_id` | UUID string | для `transfer` | Счёт назначения (обязателен при `type=transfer`) |
| `card_id` | UUID string | нет | Карта для расчёта кэшбэка (при `expense`) |

При `transfer` в `data` возвращается массив из двух транзакций.

#### GET `/` — query-параметры

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `page` | int | `1` | Страница |
| `page_size` | int | `20` | Размер страницы (1–100) |
| `type` | enum | — | `expense`, `income`, `transfer` |
| `account_id` | UUID | — | Фильтр по счёту |
| `category_id` | UUID | — | Фильтр по категории |
| `tag_id` | UUID | — | Фильтр по тегу |
| `date_from` | date | — | Начало периода |
| `date_to` | date | — | Конец периода |
| `search` | string | — | Поиск в `description` и `merchant_name` |
| `sort_by` | string | `transaction_date` | Поле сортировки |
| `sort_order` | string | `desc` | `asc` или `desc` |

#### PATCH `/{transaction_id}`

| Поле | Тип | Описание |
|------|-----|----------|
| `description` | string | Описание |
| `merchant_name` | string | Магазин |
| `notes` | string | Заметки |
| `tag_ids` | UUID[] | Полная замена списка тегов |

#### POST `/{transaction_id}/correct`

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `reason` | string | да | Причина исправления |
| `new_amount` | decimal | нет | Новая сумма (> 0) |
| `new_account_id` | UUID string | нет | Новый счёт |
| `new_category_id` | UUID string | нет | Новая категория |

Старая транзакция помечается удалённой (soft delete), создаётся новая с полем `correction_of_id`.

---

### Бюджеты — `/api/v1/budgets`

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/` | Создать бюджет |
| GET | `/` | Список бюджетов |
| GET | `/{budget_id}/status` | Потрачено, остаток, прогноз |
| PATCH | `/{budget_id}` | Обновить |
| DELETE | `/{budget_id}` | Удалить |

#### POST `/`

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `category_id` | UUID string | да | Категория расходов |
| `amount_limit` | decimal | да | Лимит, > 0 |
| `period_type` | enum | да | `weekly`, `monthly`, `yearly` |
| `start_date` | date | да | Начало действия |
| `end_date` | date | нет | Конец (опционально) |
| `rollover_enabled` | boolean | нет | Перенос остатка на следующий период, по умолчанию `false` |

#### GET `/{budget_id}/status` — ответ `data`

| Поле | Тип | Описание |
|------|-----|----------|
| `budget_id` | string | ID бюджета |
| `spent` | decimal | Потрачено за текущий период |
| `remaining` | decimal | Остаток |
| `percent_used` | float | Процент использования |
| `days_until_exceed` | int \| null | Прогноз: через сколько дней лимит будет превышен |
| `is_exceeded` | boolean | Лимит превышен |

#### PATCH `/{budget_id}`

| Поле | Тип | Описание |
|------|-----|----------|
| `amount_limit` | decimal | Новый лимит (> 0) |
| `end_date` | date | Дата окончания |
| `rollover_enabled` | boolean | Перенос остатка |

---

### Повторяющиеся операции — `/api/v1/recurring`

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/` | Создать шаблон повторяющейся операции |
| GET | `/` | Список |
| PATCH | `/{recurring_id}` | Обновить |

Выполнение по расписанию — фоновая задача Celery (`process_recurring_transactions`).

#### POST `/`

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `frequency` | enum | да | `daily`, `weekly`, `monthly`, `yearly` |
| `start_date` | date | да | Дата первого запуска |
| `account_id` | UUID string | да | Счёт |
| `type` | enum | да | `expense`, `income`, `transfer` |
| `amount` | decimal | да | Сумма, > 0 |
| `interval` | int | нет | Каждые N периодов, ≥ 1, по умолчанию `1` |
| `end_date` | date | нет | Дата окончания |
| `category_id` | UUID string | нет | Категория |
| `description` | string | нет | Описание |
| `merchant_name` | string | нет | Магазин |
| `notes` | string | нет | Заметки |

#### PATCH `/{recurring_id}`

| Поле | Тип | Описание |
|------|-----|----------|
| `is_active` | boolean | Включить / выключить |
| `end_date` | date | Дата окончания |
| `amount` | decimal | Новая сумма (> 0) |

---

### Кэшбэк — `/api/v1/cashback`

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/cards` | Привязать карту к счёту |
| GET | `/cards` | Список карт |
| POST | `/cards/{card_id}/rules` | Правило кэшбэка |
| GET | `/cards/{card_id}/rules` | Правила карты |
| GET | `/summary` | Накопленный кэшбэк |
| GET | `/missed` | Упущенный кэшбэк |
| GET | `/recommendations` | Лучшая карта для категории |

Кэшбэк начисляется автоматически при создании `expense` с указанным `category_id`.

#### POST `/cards`

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `account_id` | UUID string | да | Привязанный счёт |
| `name` | string | да | Название карты |
| `bank_name` | string | нет | Банк |
| `last_digits` | string | нет | Последние 4 цифры |

#### POST `/cards/{card_id}/rules`

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `category_id` | UUID string | да | Категория |
| `cashback_percent` | decimal | да | Процент, 0–100 |
| `start_date` | date | да | Начало действия правила |
| `monthly_limit` | decimal | нет | Лимит кэшбэка в месяц (> 0) |
| `end_date` | date | нет | Конец действия |

#### GET `/summary` — query

| Параметр | Тип | Описание |
|----------|-----|----------|
| `period_month` | string | Фильтр по месяцу `YYYY-MM` (опционально) |

#### GET `/recommendations` — query

| Параметр | Тип | Обязательно | Описание |
|----------|-----|-------------|----------|
| `category_id` | UUID | да | Категория покупки |

---

### Финансовые цели — `/api/v1/goals`

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/` | Создать цель |
| GET | `/` | Список целей |
| GET | `/{goal_id}/progress` | Прогресс |
| PATCH | `/{goal_id}` | Обновить |

Поле `current_amount` синхронизируется с балансом счёта `linked_account_id`, если он указан.

#### POST `/`

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `name` | string | да | Название цели |
| `target_amount` | decimal | да | Целевая сумма, > 0 |
| `deadline` | date | нет | Срок |
| `linked_account_id` | UUID string | нет | Счёт для отслеживания прогресса |

#### GET `/{goal_id}/progress` — ответ `data`

| Поле | Тип | Описание |
|------|-----|----------|
| `goal_id` | string | ID цели |
| `current_amount` | decimal | Текущая сумма |
| `target_amount` | decimal | Целевая сумма |
| `progress_percent` | float | Прогресс, % |
| `remaining` | decimal | Осталось накопить |
| `status` | enum | `active`, `completed`, `cancelled` |

#### PATCH `/{goal_id}`

| Поле | Тип | Описание |
|------|-----|----------|
| `name` | string | Название |
| `target_amount` | decimal | Целевая сумма (> 0) |
| `deadline` | date | Срок |
| `status` | enum | `active`, `completed`, `cancelled` |

---

### Аналитика — `/api/v1/analytics`

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/dashboard` | Сводка: баланс, доходы/расходы, цели |
| GET | `/statistics` | Топ категорий, денежный поток, средние значения |
| GET | `/heatmap` | Активность по дням (как на GitHub) |
| GET | `/ratios` | Финансовые коэффициенты |

#### GET `/statistics` и GET `/heatmap` — query

| Параметр | Тип | Описание |
|----------|-----|----------|
| `date_from` | date | Начало периода (по умолчанию ~30 / 365 дней назад) |
| `date_to` | date | Конец периода (по умолчанию — сегодня) |

#### GET `/dashboard` — основные поля `data`

`total_balance`, `total_income`, `total_expenses`, `savings_rate`, `cashback_earned`, `goals_progress[]`

#### GET `/ratios` — поля `data`

`savings_rate` — норма сбережений, `expense_to_income_ratio` — доля расходов в доходах, `discretionary_spending_ratio` — доля необязательных расходов

---

### Уведомления — `/api/v1/notifications`

In-app уведомления; создаются системой (бюджеты, повторяющиеся операции, цели, кэшбэк). Публичного POST для создания нет.

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/` | Список с пагинацией |
| PATCH | `/{notification_id}/read` | Отметить прочитанным |
| POST | `/read-all` | Отметить все прочитанными |

Типы уведомлений: `budget_warning`, `budget_exceeded`, `recurring_created`, `goal_deadline`, `cashback_available`

#### GET `/` — query

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `page` | int | `1` | Страница |
| `page_size` | int | `20` | Размер страницы (1–100) |
| `unread_only` | boolean | `false` | Только непрочитанные |

#### POST `/read-all` — ответ `data`

`{ "marked_read": <число> }`

## Тесты

**Локально** (in-memory SQLite, PostgreSQL не нужен):

```bash
pip install -r requirements-dev.txt
pytest -v
```

**Docker:**

```bash
docker compose --profile test run --rm test
```

С дополнительными аргументами pytest:

```bash
docker compose --profile test run --rm test pytest -v tests/test_auth_api.py
```

В образе `api` нет pytest — используйте сервис `test` (`Dockerfile.test`).

## Разработка

```bash
ruff check app tests
black app tests
mypy app
```

## Архитектура

- **Routes** — валидация и HTTP-слой
- **Services** — бизнес-логика
- **Repositories** — доступ к базе данных
- **Models** — только ORM-схема (без бизнес-логики)

Баланс счёта вычисляется из `ledger_entries`, а не хранится в таблице счетов. Финансовые записи удаляются мягко — поле `deleted_at`.
