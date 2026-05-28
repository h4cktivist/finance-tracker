# Finance Tracker

Приложение для учёта личных финансов: доходы и расходы, несколько счетов, бюджеты, цели, кэшбэк, аналитика и in-app уведомления. Монорепозиторий из двух частей — **backend** (FastAPI) и **frontend** (React).

| Часть | Путь | Назначение |
|-------|------|------------|
| Backend | [`backend/`](backend/) | REST API, бизнес-логика, БД, фоновые задачи |
| Frontend | [`frontend/finance-tracker/`](frontend/finance-tracker/) | SPA для пользователя |

Подробная документация API и эндпоинтов — в [backend/README.md](backend/README.md). Запуск и структура фронтенда — в [frontend/finance-tracker/README.md](frontend/finance-tracker/README.md).

---

## Возможности

### Учётная запись и безопасность

- Регистрация и вход по email и паролю
- JWT: access-токен + refresh с ротацией и отзывом при logout
- Сброс пароля (запрос токена / смена по токену; в dev режиме токен может вернуться в ответе)
- Изоляция данных: у каждого пользователя свой набор сущностей (`user_id` на всех записях)
- Rate limit на маршруты `/auth/*`

### Счета (финансовые)

- Несколько счетов на пользователя: дебетовый, кредитный, наличные, сберегательный
- Стартовый баланс (`initial_balance`) и **текущий баланс** из проводок (ledger), без хранения баланса в таблице счёта
- CRUD счетов, мягкое удаление

### Транзакции

- Типы: **расход**, **доход**, **перевод** между своими счетами
- Привязка к счёту, категории, тегам; описание, магазин, дата, заметки
- Перевод создаёт пару операций с общим `transfer_group_id`
- Список с фильтрами (тип, счёт, категория, тег, период, поиск), сортировка и пагинация
- Редактирование метаданных (описание, теги) без смены суммы и счёта
- **Исправление** (`correct`): старая операция soft-delete, новая с `correction_of_id` и при необходимости новой суммой/счётом/категорией
- Опциональная привязка карты при расходе — для расчёта кэшбэка

### Категории и теги

- Категории **расходов** и **доходов**, дерево (родитель / дочерние)
- Цвет, иконка (имя из набора Lucide), флаг «обязательный расход» для аналитики
- Теги — гибкая разметка операций, уникальны в рамках пользователя

### Бюджеты

- Лимит по категории расходов на период: неделя / месяц / год
- Статус: потрачено, остаток, % использования, прогноз превышения
- Опциональный перенос остатка на следующий период (`rollover`)
- Фоновая проверка лимитов → уведомления при приближении и превышении

### Повторяющиеся операции (подписки)

- Шаблоны: частота (день / неделя / месяц / год), интервал, сумма, счёт, категория
- Активация / пауза, дата окончания
- Celery создаёт реальные транзакции по расписанию (`next_execution_date`)

### Кэшбэк

- Карты, привязанные к счёту (банк, последние 4 цифры)
- Правила: категория → процент, период действия, месячный лимит
- Автоначисление при расходе с категорией (и опционально указанной картой)
- Сводка накопленного кэшбэка, список упущенного, рекомендация лучшей карты для категории

### Финансовые цели

- Целевая сумма, срок, статус (активна / достигнута / отменена)
- Опциональная привязка к счёту — прогресс синхронизируется с балансом счёта
- Фоновое напоминание о приближающемся дедлайне

### Аналитика

- **Дашборд**: общий баланс, доходы/расходы за месяц, норма сбережений, кэшбэк, прогресс целей
- **Статистика**: топ категорий расходов/доходов, cashflow, средние траты/доходы
- **Heatmap** активности по дням (как на GitHub)
- **Коэффициенты**: норма сбережений, доля расходов в доходах, доля необязательных трат

### Уведомления (in-app)

- Создаются системой (бюджеты, подписки, цели, кэшбэк) — публичного API создания нет
- Типы: предупреждение/превышение бюджета, создана повторяющаяся операция, дедлайн цели, доступен кэшбэк
- Список с пагинацией, фильтр непрочитанных, отметить одно / все прочитанными

### Frontend (интерфейс)

- Тёмная тема, адаптивная вёрстка (мобильное меню-drawer)
- Страницы: дашборд, транзакции, счета, категории, теги, бюджеты, подписки, кэшбэк, цели, аналитика, уведомления
- Визуальный выбор цвета (color picker) и иконок для категорий
- Графики Recharts, колокольчик уведомлений в шапке
- Автообновление access-токена при 401

---

## Архитектура

```mermaid
flowchart TB
  subgraph client [Frontend]
    SPA[React SPA :5173]
  end

  subgraph backend [Backend]
    API[FastAPI :8000]
    CW[Celery Worker]
    CB[Celery Beat]
  end

  subgraph data [Инфраструктура]
    PG[(PostgreSQL)]
    RD[(Redis)]
  end

  SPA -->|REST /api/v1| API
  API --> PG
  API --> RD
  CW --> PG
  CB --> CW
  CW --> RD
```

**Слои backend:** Routes → Services → Repositories → Models (ORM).

**Баланс счёта:** `initial_balance` + сумма проводок `ledger_entries` (двойная запись: debit/credit на операцию). Финансовые сущности удаляются мягко (`deleted_at`).

**Пользователь (`User`)** — не «отдельный модуль без связей», а владелец всех данных: JWT `sub` → фильтрация по `user_id` на каждом запросе.

---

## Стек технологий

| Backend | Frontend |
|---------|----------|
| Python 3.13+, FastAPI | React 19, TypeScript, Vite |
| PostgreSQL, SQLAlchemy 2 async | React Router, TanStack Query |
| Alembic | Axios, React Hook Form, Zod |
| Redis, Celery | Recharts, Lucide, Sonner, date-fns |
| JWT (HS256), slowapi | react-colorful |

---

## Быстрый старт (полный стек)

### Вариант 1: Docker (рекомендуется для backend)

```bash
cd backend
cp .env.example .env
docker compose up -d postgres redis --wait
docker compose run --rm --no-deps api alembic upgrade head
docker compose up -d --build
```

Поднимутся: PostgreSQL, Redis, API (`http://localhost:8000`), Celery worker и beat. Миграции применяйте вручную командой выше (или повторно после обновлений схемы).  
Документация API: [http://localhost:8000/docs](http://localhost:8000/docs)

### Вариант 2: Backend локально

Postgres и Redis в compose по умолчанию доступны только внутри Docker-сети. Для доступа с хоста один раз:

`cp docker-compose.override.example.yml docker-compose.override.yml`

```bash
cd backend
cp .env.example .env
docker compose up -d postgres redis
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend/finance-tracker
npm install
npm run dev
```

Откройте [http://localhost:5173](http://localhost:5173). Dev-сервер проксирует `/api` на `http://localhost:8000`.

Другой URL API:

```bash
VITE_API_BASE_URL=https://your-api.example.com/api/v1 npm run dev
```

### Порты по умолчанию

| Сервис | Порт на хосте |
|--------|----------------|
| Frontend (Vite) | 5173 |
| Backend API (Docker) | 8000 |
| PostgreSQL, Redis | только внутри сети compose; с хоста — через `docker-compose.override.yml` (см. `backend/docker-compose.override.example.yml`) |

---

## Фоновые задачи (Celery)

| Задача | Назначение |
|--------|------------|
| `process_recurring_transactions` | Создание транзакций из активных шаблонов подписок |
| `check_budgets` | Проверка бюджетов, уведомления о лимите |
| `check_goal_deadlines` | Напоминания о сроках целей |

Запускаются через **Celery Beat** по расписанию (нужны Redis и worker из `docker compose`).

---

## API (кратко)

- Базовый префикс: `/api/v1`
- Формат: `{ "success": true, "data": ..., "message": "" }` или `{ "success": false, "error": { "code", "message", "details" } }`
- Защищённые маршруты: заголовок `Authorization: Bearer <access_token>`

| Группа | Префикс |
|--------|---------|
| Auth | `/api/v1/auth` |
| Счета | `/api/v1/accounts` |
| Категории | `/api/v1/categories` |
| Теги | `/api/v1/tags` |
| Транзакции | `/api/v1/transactions` |
| Бюджеты | `/api/v1/budgets` |
| Подписки | `/api/v1/recurring` |
| Кэшбэк | `/api/v1/cashback` |
| Цели | `/api/v1/goals` |
| Аналитика | `/api/v1/analytics` |
| Уведомления | `/api/v1/notifications` |
| Health | `/health` |

Полные таблицы полей и query-параметров — в [backend/README.md](backend/README.md).

---

## Структура репозитория

```
finance-tracker/
├── README.md                 ← этот файл
├── backend/
│   ├── app/                  # FastAPI: api, services, models, repositories
│   ├── alembic/              # миграции БД
│   ├── tests/
│   ├── docker-compose.yml
│   └── README.md
└── frontend/
    └── finance-tracker/      # React SPA (package.json здесь)
        ├── src/
        └── README.md
```

---

## Тесты и качество кода (backend)

```bash
cd backend
pip install -r requirements-dev.txt
pytest -v
ruff check app tests
```

Docker-тесты: `docker compose --profile test run --rm test`

---

## Лицензия и статус

Pet-проект для личного учёта финансов. Перед продакшеном смените `JWT_SECRET_KEY` и пароли в `.env`, отключите `DEBUG`, настройте CORS и HTTPS.
