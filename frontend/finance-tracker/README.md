# Finance Tracker — Frontend

Полноценный фронтенд для бэкенда `Finance Tracker` (FastAPI).

## Стек

- React 19 + TypeScript
- Vite
- React Router (SPA)
- React Query — кэш и инвалидация серверных данных
- Axios — HTTP с авто-рефрешем JWT
- React Hook Form + Zod — формы и валидация
- Recharts — графики
- Sonner — тосты
- Lucide React — иконки
- date-fns — даты

## Что внутри

- Регистрация / логин / сброс пароля с JWT (access + refresh, автоматический refresh при 401)
- Дашборд: KPI-карточки, графики (Pie/Bar), heatmap активности, прогресс целей, финансовые коэффициенты
- CRUD: счета, категории (дерево), теги, бюджеты, цели, повторяющиеся транзакции
- Транзакции: фильтры, пагинация, создание (расход / доход / перевод), исправление через correction, мульти-теги, привязка карты для кэшбэка
- Кэшбэк: карты, правила, накопления, упущенный кэшбэк, рекомендации по категориям
- Аналитика с расширенными графиками за произвольный период
- Уведомления: bell в шапке + страница со списком (отметить прочитанным / все прочитаны)

## Запуск

```bash
npm install
npm run dev
```

По умолчанию dev-сервер запускается на `http://localhost:5173` и проксирует `/api/*` и `/health` на бэкенд `http://localhost:8000` (см. `vite.config.ts`).

Чтобы указать другой URL бэкенда — задайте переменную окружения:

```bash
VITE_API_BASE_URL=https://api.example.com/api/v1 npm run dev
```

## Сборка

```bash
npm run build
npm run preview
```

## Структура

```
src/
  context/        — AuthContext (JWT + user)
  hooks/          — React Query хуки на каждую сущность API
  layouts/        — AuthLayout, AppLayout (сайдбар, топбар)
  lib/            — api клиент, типы, форматирование, ошибки
  pages/          — все экраны (Dashboard, Transactions, ...)
  components/     — Modal, ConfirmDialog, EmptyState, Heatmap, NotificationsBell
  styles/         — глобальный CSS (тема, layout, формы и т.п.)
```
