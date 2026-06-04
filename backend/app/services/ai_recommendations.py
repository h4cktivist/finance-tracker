import json
from calendar import monthrange
from datetime import date
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppException, ValidationError
from app.repositories.category import CategoryRepository
from app.repositories.transaction import TransactionRepository
from app.services.analytics import AnalyticsService

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_TRANSACTIONS = 500


class AIRecommendationsService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.tx_repo = TransactionRepository(session)
        self.category_repo = CategoryRepository(session)
        self.analytics = AnalyticsService(session)

    @staticmethod
    def _parse_month(month: str) -> tuple[date, date]:
        parts = month.strip().split("-")
        if len(parts) != 2:
            raise ValidationError("month должен быть в формате YYYY-MM")
        try:
            year = int(parts[0])
            mon = int(parts[1])
        except ValueError as exc:
            raise ValidationError("month должен быть в формате YYYY-MM") from exc
        if not (1 <= mon <= 12):
            raise ValidationError("Некорректный месяц")
        last_day = monthrange(year, mon)[1]
        return date(year, mon, 1), date(year, mon, last_day)

    async def generate(self, user_id: UUID, month: str) -> str:
        settings = get_settings()
        if not settings.openrouter_api_key:
            raise AppException(
                message="Сервис рекомендаций не настроен (OPENROUTER_API_KEY)",
                code="AI_NOT_CONFIGURED",
                status_code=503,
            )

        date_from, date_to = self._parse_month(month)
        if date_from > date.today():
            raise ValidationError("Нельзя запросить рекомендации для будущего месяца")

        transactions, total = await self.tx_repo.list_filtered(
            user_id,
            page=1,
            page_size=MAX_TRANSACTIONS,
            date_from=date_from,
            date_to=date_to,
            sort_by="transaction_date",
            sort_order="asc",
        )
        categories = await self.category_repo.list_by_user(user_id)
        category_names = {c.id: c.name for c in categories}

        stats = await self.analytics.statistics(user_id, date_from, date_to)
        income, expenses = await self.analytics._sum_income_expenses(user_id, date_from, date_to, [])
        context = self._build_context(
            month=month,
            date_from=date_from,
            date_to=date_to,
            transactions=transactions,
            total_transactions=total,
            category_names=category_names,
            stats=stats,
            total_income=income,
            total_expenses=expenses,
        )
        return await self._call_openrouter(settings.openrouter_api_key, settings.openrouter_model, context)

    def _build_context(
        self,
        *,
        month: str,
        date_from: date,
        date_to: date,
        transactions: list,
        total_transactions: int,
        category_names: dict,
        stats,
        total_income,
        total_expenses,
    ) -> str:
        tx_lines = []
        for tx in transactions:
            cat = category_names.get(tx.category_id, "Без категории") if tx.category_id else "Без категории"
            desc = tx.description or tx.merchant_name or "—"
            tx_lines.append(
                f"- {tx.transaction_date.isoformat()} | {tx.type.value} | {cat} | "
                f"{tx.amount} ₽ | {desc}"
            )

        top_expense = [
            {"category": c.category_name, "total": str(c.total)}
            for c in (stats.top_expense_categories or [])[:8]
        ]
        top_income = [
            {"category": c.category_name, "total": str(c.total)}
            for c in (stats.top_income_categories or [])[:8]
        ]

        payload = {
            "month": month,
            "period": f"{date_from.isoformat()} — {date_to.isoformat()}",
            "summary": {
                "total_income": str(total_income),
                "total_expenses": str(total_expenses),
                "cashflow": str(stats.cashflow),
                "average_daily_spending": str(stats.average_daily_spending),
                "transaction_count": total_transactions,
                "transactions_in_prompt": len(transactions),
                "truncated": total_transactions > len(transactions),
            },
            "top_expense_categories": top_expense,
            "top_income_categories": top_income,
            "transactions": tx_lines,
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    async def _call_openrouter(self, api_key: str, model: str, context: str) -> str:
        system = (
            "Ты персональный финансовый советник. На основе данных о транзакциях пользователя "
            "за месяц дай практичные рекомендации на русском языке. "
            "Используй markdown: заголовки (##), маркированные списки. "
            "Выводи только рекомендации — без вступлений про то, что ты ИИ. "
            "Опирайся на конкретные цифры из данных. "
            "Структурируй ответ блоками: обзор месяца, что хорошо, на что обратить внимание, "
            "конкретные шаги на следующий месяц."
        )
        user_msg = f"Данные за месяц (JSON):\n\n{context}"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://finance-tracker.local",
            "X-Title": "Finance Tracker",
        }
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            "temperature": 0.6,
            "max_tokens": 2048,
        }

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(OPENROUTER_URL, headers=headers, json=body)
        except httpx.TimeoutException as exc:
            raise AppException(
                message="Превышено время ожидания ответа от ИИ",
                code="AI_TIMEOUT",
                status_code=504,
            ) from exc
        except httpx.HTTPError as exc:
            raise AppException(
                message="Не удалось связаться с сервисом ИИ",
                code="AI_NETWORK_ERROR",
                status_code=502,
            ) from exc

        if response.status_code != 200:
            detail = response.text[:500]
            raise AppException(
                message="Сервис ИИ вернул ошибку",
                code="AI_PROVIDER_ERROR",
                status_code=502,
                details={"status": response.status_code, "body": detail},
            )

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AppException(
                message="Некорректный ответ от сервиса ИИ",
                code="AI_INVALID_RESPONSE",
                status_code=502,
            ) from exc

        if not content or not str(content).strip():
            raise AppException(
                message="Сервис ИИ вернул пустой ответ",
                code="AI_EMPTY_RESPONSE",
                status_code=502,
            )
        return str(content).strip()
