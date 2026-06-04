from calendar import monthrange
from datetime import date
from decimal import Decimal, ROUND_CEILING
from typing import Literal
from uuid import UUID

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget, BudgetPeriodType
from app.models.category import Category, CategoryType
from app.models.transaction import Transaction, TransactionType
from app.repositories.budget import BudgetRepository
from app.schemas.budget import BudgetRecommendationItem, BudgetRecommendationsResponse

RecommendationType = Literal["create", "increase", "decrease"]

HISTORY_MONTHS = 3
MIN_TOTAL_SPEND = Decimal("500")
MIN_TRANSACTIONS = 2
HEADROOM = Decimal("1.15")
INCREASE_USAGE_RATIO = Decimal("0.90")
DECREASE_USAGE_RATIO = Decimal("0.45")
ROUND_TO = Decimal("10")


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    last_day = monthrange(year, month)[1]
    return start, date(year, month, last_day)


def _history_range() -> tuple[date, date, list[tuple[int, int]]]:
    today = date.today()
    months: list[tuple[int, int]] = []
    y, m = today.year, today.month
    for _ in range(HISTORY_MONTHS):
        months.append((y, m))
        m -= 1
        if m < 1:
            m = 12
            y -= 1
    months.reverse()
    first_start, _ = _month_bounds(months[0][0], months[0][1])
    _, last_end = _month_bounds(months[-1][0], months[-1][1])
    return first_start, last_end, months


def _round_limit(amount: Decimal) -> Decimal:
    if amount <= 0:
        return ROUND_TO
    return (amount / ROUND_TO).quantize(Decimal("1"), rounding=ROUND_CEILING) * ROUND_TO


def _monthly_equivalent_limit(budget: Budget) -> Decimal:
    if budget.period_type == BudgetPeriodType.MONTHLY:
        return budget.amount_limit
    if budget.period_type == BudgetPeriodType.WEEKLY:
        return budget.amount_limit * Decimal("52") / Decimal("12")
    return budget.amount_limit / Decimal("12")


def _suggest_limit(avg_monthly: Decimal, max_monthly: Decimal) -> Decimal:
    base = max(avg_monthly, max_monthly * Decimal("0.85"))
    return _round_limit(base * HEADROOM)


class BudgetRecommendationsService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.budget_repo = BudgetRepository(session)

    async def recommend(self, user_id: UUID) -> BudgetRecommendationsResponse:
        date_from, date_to, calendar_months = _history_range()
        rows = await self._fetch_monthly_expense_rows(user_id, date_from, date_to)
        budgets = await self.budget_repo.list_by_user(user_id)
        budget_by_category = self._budgets_by_category(budgets)

        by_category: dict[UUID, dict] = {}
        for cat_id, cat_name, year, month, total, tx_count in rows:
            entry = by_category.setdefault(
                cat_id,
                {
                    "name": cat_name,
                    "monthly": {ym: Decimal("0") for ym in calendar_months},
                    "tx_count": 0,
                },
            )
            ym = (int(year), int(month))
            if ym in entry["monthly"]:
                entry["monthly"][ym] += Decimal(str(total))
            entry["tx_count"] += int(tx_count)

        items: list[BudgetRecommendationItem] = []
        for cat_id, data in by_category.items():
            monthly_values = list(data["monthly"].values())
            total_spent = sum(monthly_values, Decimal("0"))
            tx_count = data["tx_count"]
            if total_spent < MIN_TOTAL_SPEND or tx_count < MIN_TRANSACTIONS:
                continue

            active_months = [v for v in monthly_values if v > 0]
            months_with_activity = len(active_months)
            if months_with_activity == 0:
                continue

            avg_monthly = sum(monthly_values, Decimal("0")) / len(monthly_values)
            max_monthly = max(monthly_values)
            suggested = _suggest_limit(avg_monthly, max_monthly)
            avg_tx_per_month = tx_count / max(months_with_activity, 1)

            budget = budget_by_category.get(cat_id)
            if budget is None:
                items.append(
                    self._item(
                        cat_id=cat_id,
                        name=data["name"],
                        rec_type="create",
                        suggested=suggested,
                        avg_monthly=avg_monthly,
                        max_monthly=max_monthly,
                        tx_count=tx_count,
                        months_with_activity=months_with_activity,
                        avg_tx_per_month=avg_tx_per_month,
                        budget=None,
                    )
                )
                continue

            if budget.period_type != BudgetPeriodType.MONTHLY:
                continue

            limit_monthly = _monthly_equivalent_limit(budget)
            if limit_monthly <= 0:
                continue

            usage = avg_monthly / limit_monthly
            if usage >= INCREASE_USAGE_RATIO and suggested > budget.amount_limit:
                items.append(
                    self._item(
                        cat_id=cat_id,
                        name=data["name"],
                        rec_type="increase",
                        suggested=suggested,
                        avg_monthly=avg_monthly,
                        max_monthly=max_monthly,
                        tx_count=tx_count,
                        months_with_activity=months_with_activity,
                        avg_tx_per_month=avg_tx_per_month,
                        budget=budget,
                        usage_ratio=float(usage),
                    )
                )
            elif usage <= DECREASE_USAGE_RATIO and suggested < budget.amount_limit:
                items.append(
                    self._item(
                        cat_id=cat_id,
                        name=data["name"],
                        rec_type="decrease",
                        suggested=suggested,
                        avg_monthly=avg_monthly,
                        max_monthly=max_monthly,
                        tx_count=tx_count,
                        months_with_activity=months_with_activity,
                        avg_tx_per_month=avg_tx_per_month,
                        budget=budget,
                        usage_ratio=float(usage),
                    )
                )

        items.sort(key=lambda x: x.avg_monthly_spent, reverse=True)
        return BudgetRecommendationsResponse(
            items=items[:12],
            period_from=date_from,
            period_to=date_to,
            months_analyzed=HISTORY_MONTHS,
        )

    async def _fetch_monthly_expense_rows(
        self, user_id: UUID, date_from: date, date_to: date
    ) -> list[tuple[UUID, str, int, int, Decimal, int]]:
        year_col = extract("year", Transaction.transaction_date)
        month_col = extract("month", Transaction.transaction_date)
        result = await self.session.execute(
            select(
                Category.id,
                Category.name,
                year_col,
                month_col,
                func.coalesce(func.sum(Transaction.amount), 0),
                func.count(Transaction.id),
            )
            .join(Transaction, Transaction.category_id == Category.id)
            .where(
                Transaction.user_id == user_id,
                Transaction.type == TransactionType.EXPENSE,
                Transaction.deleted_at.is_(None),
                Transaction.transaction_date >= date_from,
                Transaction.transaction_date <= date_to,
                Category.user_id == user_id,
                Category.type == CategoryType.EXPENSE,
                Category.deleted_at.is_(None),
                Transaction.category_id.isnot(None),
            )
            .group_by(Category.id, Category.name, year_col, month_col)
        )
        return [
            (
                row[0],
                row[1],
                int(row[2]),
                int(row[3]),
                Decimal(str(row[4])),
                int(row[5]),
            )
            for row in result.all()
        ]

    @staticmethod
    def _budgets_by_category(budgets: list[Budget]) -> dict[UUID, Budget]:
        by_cat: dict[UUID, Budget] = {}
        for budget in budgets:
            existing = by_cat.get(budget.category_id)
            if existing is None:
                by_cat[budget.category_id] = budget
            elif budget.period_type == BudgetPeriodType.MONTHLY:
                by_cat[budget.category_id] = budget
        return by_cat

    @staticmethod
    def _item(
        *,
        cat_id: UUID,
        name: str,
        rec_type: RecommendationType,
        suggested: Decimal,
        avg_monthly: Decimal,
        max_monthly: Decimal,
        tx_count: int,
        months_with_activity: int,
        avg_tx_per_month: float,
        budget: Budget | None,
        usage_ratio: float | None = None,
    ) -> BudgetRecommendationItem:
        if rec_type == "create":
            reason = (
                f"За {HISTORY_MONTHS} мес.: в среднем {avg_monthly:.0f} ₽/мес., "
                f"пик {max_monthly:.0f} ₽, ~{avg_tx_per_month:.1f} операций в месяц "
                f"({tx_count} всего). Бюджета по категории нет."
            )
        elif rec_type == "increase":
            pct = int((usage_ratio or 0) * 100)
            reason = (
                f"Средние траты ~{avg_monthly:.0f} ₽/мес. — около {pct}% от лимита "
                f"{budget.amount_limit:.0f} ₽. Рекомендуем запас ~{int(HEADROOM * 100 - 100)}%."
            )
        else:
            pct = int((usage_ratio or 0) * 100)
            reason = (
                f"Средние траты ~{avg_monthly:.0f} ₽/мес. — лишь {pct}% лимита "
                f"{budget.amount_limit:.0f} ₽. Лимит можно снизить без риска перерасхода."
            )

        return BudgetRecommendationItem(
            category_id=str(cat_id),
            category_name=name,
            recommendation_type=rec_type,
            suggested_amount_limit=suggested,
            suggested_period_type=BudgetPeriodType.MONTHLY,
            avg_monthly_spent=avg_monthly,
            max_monthly_spent=max_monthly,
            transaction_count=tx_count,
            months_with_activity=months_with_activity,
            existing_budget_id=str(budget.id) if budget else None,
            current_amount_limit=budget.amount_limit if budget else None,
            reason=reason,
        )
