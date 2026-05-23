# Personal Finance Tracker Backend Specification

# Project Overview

Develop a production-ready backend for a personal finance and budgeting web application.

The system should support:
- personal finance tracking;
- budgeting;
- recurring transactions;
- cashback management;
- financial goals;
- analytics/statistics;
- notification system;
- secure financial data handling.

The backend must be designed with scalability, maintainability, and clean architecture in mind.

---

# Tech Stack

## Core Stack

- Python 3.13+
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0 (async)
- Alembic
- Pydantic v2
- Redis
- Celery (or Dramatiq)
- Docker + Docker Compose

---

# Recommended Additional Libraries

## Authentication & Security

- passlib[bcrypt]
- python-jose
- PyJWT
- slowapi (rate limiting)

---

## Database

- asyncpg
- sqlalchemy-utils

---

## Validation & Settings

- pydantic-settings

---

## Background Jobs

- Celery + Redis broker

Used for:
- recurring transactions;
- notifications;
- analytics recalculation;
- scheduled cashback processing.

---

## Testing

- pytest
- pytest-asyncio
- factory-boy

---

# Architecture Requirements

Use clean modular architecture.

Recommended structure:

```text
app/
├── api/
├── core/
├── db/
├── models/
├── schemas/
├── services/
├── repositories/
├── tasks/
├── analytics/
├── cashback/
├── notifications/
├── auth/
├── utils/
└── tests/
```

---

# Architectural Principles

## 1. Async-first architecture

Use:
- async SQLAlchemy;
- async FastAPI endpoints;
- async database sessions.

---

## 2. Repository + Service Layer

Do NOT put business logic inside routes.

Routes:
- validation;
- response handling.

Services:
- business logic.

Repositories:
- database access.

---

## 3. Financial Data Integrity

Financial operations must be:
- transactional;
- atomic;
- auditable.

---

## 4. Soft Delete

Never physically delete financial records.

Use:
```sql
deleted_at TIMESTAMP NULL
```

---

## 5. Audit Log

All critical operations must be logged.

Including:
- create/update/delete;
- login;
- password changes;
- budget updates;
- transaction modifications.

---

## 6. Double-entry Accounting

Transfers between accounts must create:
- debit entry;
- credit entry.

Balances should never be treated as the source of truth.

Balance must be calculated from transactions.

---

# Main Functional Modules

---

# 1. Authentication Module

## Features

- JWT authentication;
- refresh tokens;
- password hashing;
- email/password login;
- optional email verification.

---

## Endpoints

```http
POST /auth/register
POST /auth/login
POST /auth/refresh
POST /auth/logout
POST /auth/reset-password
```

---

# 2. Accounts Module

Represents:
- debit cards;
- credit cards;
- cash;
- savings accounts.

---

## Account Fields

```text
id
user_id
name
type
currency
initial_balance
created_at
updated_at
deleted_at
```

---

## Features

- CRUD accounts;
- account balances;
- transfers between accounts.

---

# 3. Categories Module

## Types

- expense;
- income.

---

## Features

- nested categories;
- colors;
- icons;
- hierarchy support.

---

## Category Fields

```text
id
user_id
name
type
parent_category_id
color
icon
created_at
updated_at
deleted_at
```

---

# 4. Tags Module

Additional transaction classification.

Examples:
- vacation;
- work;
- subscription.

---

# 5. Transactions Module

## Transaction Types

- expense;
- income;
- transfer.

---

## Transaction Fields

```text
id
user_id
account_id
category_id
type
amount
currency
description
merchant_name
transaction_date
notes
created_at
updated_at
deleted_at
```

---

## Features

- CRUD operations;
- pagination;
- filtering;
- sorting;
- tag support;
- search;
- transfer handling.

---

## Important Rules

### Expenses
Must reduce account balance.

### Income
Must increase account balance.

### Transfers
Must create paired entries.

---

# 6. Recurring Transactions Module

Automatically creates transactions on schedule.

---

## Supported Frequencies

- daily;
- weekly;
- monthly;
- yearly.

---

## Fields

```text
id
user_id
template_transaction_id
frequency
interval
start_date
end_date
next_execution_date
is_active
created_at
```

---

## Background Jobs

Scheduler must:
- find due recurring transactions;
- create actual transactions;
- update next_execution_date.

---

# 7. Budgets Module

## Features

- category budgets;
- monthly/weekly/yearly budgets;
- rollover budgets;
- budget alerts.

---

## Budget Fields

```text
id
user_id
category_id
amount_limit
period_type
start_date
end_date
rollover_enabled
created_at
updated_at
```

---

## Budget Forecasting

Implement simple forecasting:
```text
If spending pace continues,
budget will be exceeded in X days.
```

No ML required.

---

# 8. Financial Goals Module

## Features

- savings goals;
- progress tracking;
- target deadlines.

---

## Goal Fields

```text
id
user_id
name
target_amount
current_amount
deadline
linked_account_id
status
created_at
updated_at
```

---

# 9. Cashback System

One of the key features.

---

# Cards Module

Represents real user bank cards.

---

## Card Fields

```text
id
user_id
account_id
name
bank_name
last_digits
created_at
```

---

# Cashback Rules

Each card may have:
- category cashback;
- cashback percent;
- monthly limits;
- active periods.

---

## Cashback Rule Fields

```text
id
card_id
category_id
cashback_percent
monthly_limit
start_date
end_date
```

---

# Cashback Logic

When creating transaction:
1. detect category;
2. find applicable cashback rules;
3. calculate cashback;
4. determine best card.

---

## Features

- accumulated cashback;
- cashback statistics;
- missed cashback;
- best card recommendations.

---

# 10. Analytics Module

---

# Dashboard Metrics

- total balance;
- income vs expenses;
- savings rate;
- cashback earned;
- goals progress.

---

# Statistics

- top spending categories;
- top income categories;
- cashflow;
- average daily spending;
- average monthly income.

---

# Heatmap Analytics

Implement GitHub-style activity heatmap:
- transaction activity;
- spending intensity.

---

# Financial Ratios

## Savings Rate

```text
(Income - Expenses) / Income
```

---

## Expense-to-Income Ratio

```text
Expenses / Income
```

---

## Discretionary Spending Ratio

```text
Non-essential Expenses / Income
```

---

# 11. Notifications Module

## Notification Types

- budget exceeded;
- budget warning;
- recurring transaction created;
- goal deadline warning;
- cashback available.

---

## Channels

- in-app;
- email (optional);
- Telegram (future).

---

# Security Requirements

## Required

- bcrypt password hashing;
- JWT rotation;
- secure cookies;
- CSRF protection;
- rate limiting;
- HTTPS-only;
- input validation.

---

# Database Requirements

Use PostgreSQL.

---

# Important Constraints

## All tables must include:

```sql
created_at TIMESTAMP
updated_at TIMESTAMP
```

Financial tables additionally:

```sql
deleted_at TIMESTAMP NULL
```

---

## Use UUID primary keys

Example:

```sql
id UUID PRIMARY KEY
```

---

## Add indexes

Especially for:
- user_id;
- transaction_date;
- category_id;
- account_id.

---

# API Requirements

## Standards

- REST API;
- JSON responses;
- OpenAPI documentation;
- versioned API:
```text
/api/v1/
```

---

## Response Format

Standardized responses:

```json
{
  "success": true,
  "data": {},
  "message": ""
}
```

---

# Error Handling

Use centralized exception handlers.

Example:

```json
{
  "success": false,
  "error": {
    "code": "BUDGET_EXCEEDED",
    "message": "Budget exceeded"
  }
}
```

---

# Performance Requirements

- API response time < 300ms;
- support 10k+ transactions per user;
- optimized analytics queries;
- proper database indexing.

---

# Suggested PostgreSQL Features

Use:
- JSONB where appropriate;
- partial indexes;
- materialized views for analytics;
- generated columns if useful.

---

# Future-ready Requirements

Architecture should allow future integration of:
- Open Banking APIs;
- OCR receipt parsing;
- ML transaction categorization;
- AI insights;
- family/shared budgets;
- investment tracking.

---

# Docker Requirements

Provide:
- Dockerfile;
- docker-compose.yml;
- separate services:
  - backend;
  - postgres;
  - redis;
  - celery worker.

---

# Development Standards

## Code Quality

- type hints everywhere;
- Ruff linter;
- Black formatter;
- mypy support.

---

## Testing

Must include:
- unit tests;
- integration tests;
- async endpoint tests.

---

# Initial MVP Scope

Implement list:

1. Authentication
2. Accounts
3. Categories
4. Transactions
5. Budgets
6. Recurring Transactions
7. Basic Analytics
8. Cashback System
9. Financial Goals
10. Audit Logs

---

# Important Implementation Notes

## Transactions must be immutable where possible

Avoid destructive updates.

Prefer:
- audit history;
- correction entries.

---

## Avoid business logic in ORM models

Business logic belongs in services.

---

## Prefer composition over inheritance

Keep models simple and explicit.

---

# Expected Deliverables

- production-ready backend;
- Dockerized environment;
- PostgreSQL schema;
- Alembic migrations;
- OpenAPI docs;
- tests;
- modular scalable architecture.