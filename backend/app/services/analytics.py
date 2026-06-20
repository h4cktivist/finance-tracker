from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from app.models.category import Category, CategoryType
from app.models.transaction import Transaction, TransactionType
from app.repositories.account import AccountRepository
from app.repositories.cashback import CashbackAccrualRepository
from app.repositories.category import CategoryRepository
from app.repositories.goal import GoalRepository
from app.repositories.ledger import LedgerRepository
from app.schemas.analytics import (
    CategoryMerchants,
    CategoryStat,
    DashboardResponse,
    HeatmapDay,
    HeatmapResponse,
    MerchantStat,
    MerchantsResponse,
    RatiosResponse,
    StatisticsResponse,
    TrendPoint,
    TrendsResponse,
)
from app.services.goal import GoalService

INVESTMENT_EXPENSE_CATEGORY_NAME = "Инвестиции"


class AnalyticsService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.account_repo = AccountRepository(session)
        self.ledger_repo = LedgerRepository(session)
        self.category_repo = CategoryRepository(session)
        self.cashback_repo = CashbackAccrualRepository(session)
        self.goal_repo = GoalRepository(session)
        self.goal_service = GoalService(session)

    async def _investment_expense_category_ids(self, user_id: UUID) -> list[UUID]:
        result = await self.session.execute(
            select(Category.id).where(
                Category.user_id == user_id,
                Category.name == INVESTMENT_EXPENSE_CATEGORY_NAME,
                Category.type == CategoryType.EXPENSE,
                Category.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())

    def _exclude_investment_expense_clause(
        self, category_ids: list[UUID]
    ) -> ColumnElement[bool]:
        return or_(
            Transaction.type != TransactionType.EXPENSE,
            Transaction.category_id.is_(None),
            Transaction.category_id.notin_(category_ids),
        )

    async def dashboard(
        self, user_id: UUID, *, exclude_investments: bool = False
    ) -> DashboardResponse:
        accounts = await self.account_repo.list_by_user(user_id)
        total_balance = Decimal("0")
        for acc in accounts:
            balance = await self.ledger_repo.get_account_balance(acc.id, acc.initial_balance)
            total_balance += balance
        today = date.today()
        month_start = today.replace(day=1)
        investment_ids = (
            await self._investment_expense_category_ids(user_id) if exclude_investments else []
        )
        income, expenses = await self._sum_income_expenses(
            user_id, month_start, today, investment_ids
        )
        savings_rate = float((income - expenses) / income * 100) if income > 0 else 0.0
        cashback = await self.cashback_repo.total_earned(user_id)
        goals = await self.goal_repo.list_by_user(user_id)
        for goal in goals:
            await self.goal_service.sync_progress(goal)
        goals_progress = [
            {
                "goal_id": str(goal.id),
                "name": goal.name,
                "progress_percent": (
                    float(goal.current_amount / goal.target_amount * 100)
                    if goal.target_amount > 0
                    else 0.0
                ),
            }
            for goal in goals
        ]
        return DashboardResponse(
            total_balance=total_balance,
            total_income=income,
            total_expenses=expenses,
            savings_rate=savings_rate,
            cashback_earned=cashback,
            goals_progress=goals_progress,
        )

    async def statistics(
        self,
        user_id: UUID,
        date_from: date | None = None,
        date_to: date | None = None,
        *,
        exclude_investments: bool = False,
    ) -> StatisticsResponse:
        date_to = date_to or date.today()
        date_from = date_from or date_to - timedelta(days=30)
        investment_ids = (
            await self._investment_expense_category_ids(user_id) if exclude_investments else []
        )
        top_expense = await self._top_categories(
            user_id,
            date_from,
            date_to,
            TransactionType.EXPENSE,
            investment_ids=investment_ids,
        )
        top_income = await self._top_categories(user_id, date_from, date_to, TransactionType.INCOME)
        income, expenses = await self._sum_income_expenses(
            user_id, date_from, date_to, investment_ids
        )
        days = (date_to - date_from).days + 1
        months = max(days / 30, 1)
        return StatisticsResponse(
            top_expense_categories=top_expense,
            top_income_categories=top_income,
            cashflow=income - expenses,
            average_daily_spending=expenses / days if days else Decimal("0"),
            average_monthly_income=income / Decimal(str(months)),
        )

    async def merchants(
        self,
        user_id: UUID,
        date_from: date | None = None,
        date_to: date | None = None,
        *,
        exclude_investments: bool = False,
        limit_categories: int = 6,
        limit_merchants: int = 6,
    ) -> MerchantsResponse:
        date_to = date_to or date.today()
        date_from = date_from or date_to - timedelta(days=30)
        investment_ids = (
            await self._investment_expense_category_ids(user_id) if exclude_investments else []
        )
        merchant_filters = [
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.deleted_at.is_(None),
            Transaction.merchant_name.is_not(None),
            Transaction.transaction_date >= date_from,
            Transaction.transaction_date <= date_to,
            Category.deleted_at.is_(None),
        ]
        if investment_ids:
            merchant_filters.append(Category.id.notin_(investment_ids))
        result = await self.session.execute(
            select(
                Category.id,
                Category.name,
                Category.color,
                Transaction.merchant_name,
                func.sum(Transaction.amount),
                func.count(Transaction.id),
            )
            .join(Transaction, Transaction.category_id == Category.id)
            .where(*merchant_filters)
            .group_by(Category.id, Category.name, Category.color, Transaction.merchant_name)
        )
        by_category: dict[UUID, dict] = {}
        for cat_id, cat_name, color, merchant_name, total, count in result.all():
            bucket = by_category.setdefault(
                cat_id,
                {"category_name": cat_name, "color": color, "total": Decimal("0"), "merchants": []},
            )
            amount = Decimal(str(total))
            bucket["total"] += amount
            bucket["merchants"].append(
                MerchantStat(merchant_name=merchant_name, total=amount, count=count)
            )
        categories = [
            CategoryMerchants(
                category_id=str(cat_id),
                category_name=data["category_name"],
                color=data["color"],
                total=data["total"],
                merchants=sorted(data["merchants"], key=lambda m: m.total, reverse=True)[
                    :limit_merchants
                ],
            )
            for cat_id, data in by_category.items()
        ]
        categories.sort(key=lambda c: c.total, reverse=True)
        return MerchantsResponse(categories=categories[:limit_categories])

    async def heatmap(
        self,
        user_id: UUID,
        date_from: date | None = None,
        date_to: date | None = None,
        *,
        exclude_investments: bool = False,
    ) -> HeatmapResponse:
        date_to = date_to or date.today()
        date_from = date_from or date_to - timedelta(days=365)
        investment_ids = (
            await self._investment_expense_category_ids(user_id) if exclude_investments else []
        )
        heatmap_filters = [
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
            Transaction.transaction_date >= date_from,
            Transaction.transaction_date <= date_to,
        ]
        if investment_ids:
            heatmap_filters.append(self._exclude_investment_expense_clause(investment_ids))
        result = await self.session.execute(
            select(
                Transaction.transaction_date,
                func.count(Transaction.id),
                func.coalesce(func.sum(Transaction.amount), 0),
            )
            .where(*heatmap_filters)
            .group_by(Transaction.transaction_date)
            .order_by(Transaction.transaction_date)
        )
        rows = result.all()
        max_amount = max((Decimal(str(r[2])) for r in rows), default=Decimal("1"))
        days = [
            HeatmapDay(
                date=r[0].isoformat(),
                count=r[1],
                total_amount=Decimal(str(r[2])),
                intensity=float(Decimal(str(r[2])) / max_amount) if max_amount else 0.0,
            )
            for r in rows
        ]
        return HeatmapResponse(days=days)

    async def trends(
        self,
        user_id: UUID,
        date_from: date | None = None,
        date_to: date | None = None,
        *,
        exclude_investments: bool = False,
    ) -> TrendsResponse:
        date_to = date_to or date.today()
        date_from = date_from or date_to.replace(day=1)
        investment_ids = (
            await self._investment_expense_category_ids(user_id) if exclude_investments else []
        )
        trend_filters = [
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
            Transaction.transaction_date >= date_from,
            Transaction.transaction_date <= date_to,
            Transaction.type.in_([TransactionType.INCOME, TransactionType.EXPENSE]),
        ]
        if investment_ids:
            trend_filters.append(self._exclude_investment_expense_clause(investment_ids))
        result = await self.session.execute(
            select(
                Transaction.transaction_date,
                Transaction.type,
                func.coalesce(func.sum(Transaction.amount), 0),
            )
            .where(*trend_filters)
            .group_by(Transaction.transaction_date, Transaction.type)
            .order_by(Transaction.transaction_date)
        )
        by_date: dict[date, dict[str, Decimal]] = {}
        for tx_date, tx_type, total in result.all():
            day = by_date.setdefault(tx_date, {"income": Decimal("0"), "expenses": Decimal("0")})
            amount = Decimal(str(total))
            if tx_type == TransactionType.INCOME:
                day["income"] = amount
            else:
                day["expenses"] = amount
        points: list[TrendPoint] = []
        current = date_from
        while current <= date_to:
            totals = by_date.get(current, {"income": Decimal("0"), "expenses": Decimal("0")})
            points.append(
                TrendPoint(
                    date=current.isoformat(),
                    income=totals["income"],
                    expenses=totals["expenses"],
                )
            )
            current += timedelta(days=1)
        return TrendsResponse(points=points)

    async def ratios(self, user_id: UUID, *, exclude_investments: bool = False) -> RatiosResponse:
        today = date.today()
        month_start = today.replace(day=1)
        investment_ids = (
            await self._investment_expense_category_ids(user_id) if exclude_investments else []
        )
        income, expenses = await self._sum_income_expenses(
            user_id, month_start, today, investment_ids
        )
        savings_rate = float((income - expenses) / income) if income > 0 else 0.0
        expense_ratio = float(expenses / income) if income > 0 else 0.0
        discretionary = await self._discretionary_expenses(
            user_id, month_start, today, investment_ids
        )
        discretionary_ratio = float(discretionary / income) if income > 0 else 0.0
        return RatiosResponse(
            savings_rate=savings_rate,
            expense_to_income_ratio=expense_ratio,
            discretionary_spending_ratio=discretionary_ratio,
        )

    async def _sum_income_expenses(
        self,
        user_id: UUID,
        date_from: date,
        date_to: date,
        investment_category_ids: list[UUID] | None = None,
    ) -> tuple[Decimal, Decimal]:
        filters = [
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
            Transaction.transaction_date >= date_from,
            Transaction.transaction_date <= date_to,
            Transaction.type.in_([TransactionType.INCOME, TransactionType.EXPENSE]),
        ]
        if investment_category_ids:
            filters.append(self._exclude_investment_expense_clause(investment_category_ids))
        result = await self.session.execute(
            select(Transaction.type, func.coalesce(func.sum(Transaction.amount), 0))
            .where(*filters)
            .group_by(Transaction.type)
        )
        income = Decimal("0")
        expenses = Decimal("0")
        for tx_type, total in result.all():
            if tx_type == TransactionType.INCOME:
                income = Decimal(str(total))
            else:
                expenses = Decimal(str(total))
        return (income, expenses)

    async def _top_categories(
        self,
        user_id: UUID,
        date_from: date,
        date_to: date,
        tx_type: TransactionType,
        limit: int = 10,
        *,
        investment_ids: list[UUID] | None = None,
    ) -> list[CategoryStat]:
        category_filters = [
            Transaction.user_id == user_id,
            Transaction.type == tx_type,
            Transaction.deleted_at.is_(None),
            Transaction.transaction_date >= date_from,
            Transaction.transaction_date <= date_to,
            Category.deleted_at.is_(None),
        ]
        if investment_ids and tx_type == TransactionType.EXPENSE:
            category_filters.append(Category.id.notin_(investment_ids))
        result = await self.session.execute(
            select(
                Category.id,
                Category.name,
                Category.color,
                func.coalesce(func.sum(Transaction.amount), 0),
            )
            .join(Transaction, Transaction.category_id == Category.id)
            .where(*category_filters)
            .group_by(Category.id, Category.name, Category.color)
            .order_by(func.sum(Transaction.amount).desc())
            .limit(limit)
        )
        return [
            CategoryStat(
                category_id=str(row[0]),
                category_name=row[1],
                color=row[2],
                total=Decimal(str(row[3])),
            )
            for row in result.all()
        ]

    async def _discretionary_expenses(
        self,
        user_id: UUID,
        date_from: date,
        date_to: date,
        investment_category_ids: list[UUID] | None = None,
    ) -> Decimal:
        discretionary_filters = [
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.deleted_at.is_(None),
            Transaction.transaction_date >= date_from,
            Transaction.transaction_date <= date_to,
            Category.is_essential.is_(False),
            Category.deleted_at.is_(None),
        ]
        if investment_category_ids:
            discretionary_filters.append(Category.id.notin_(investment_category_ids))
        result = await self.session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .join(Category, Transaction.category_id == Category.id)
            .where(*discretionary_filters)
        )
        return Decimal(str(result.scalar_one()))
