from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.models.budget import Budget, BudgetPeriodType
from app.models.transaction import TransactionType
from app.models.user import User
from app.repositories.budget import BudgetRepository
from app.repositories.category import CategoryRepository
from app.repositories.transaction import TransactionRepository
from app.schemas.budget import BudgetCreate, BudgetStatusResponse, BudgetUpdate
from app.services.audit import AuditService
from app.services.notification import NotificationService

settings = get_settings()


class BudgetService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = BudgetRepository(session)
        self.tx_repo = TransactionRepository(session)
        self.category_repo = CategoryRepository(session)
        self.audit = AuditService(session)
        self.notifications = NotificationService(session)

    def _period_bounds(self, budget: Budget, ref: date | None = None) -> tuple[date, date]:
        ref = ref or date.today()
        if budget.period_type == BudgetPeriodType.WEEKLY:
            start = ref - timedelta(days=ref.weekday())
            end = start + timedelta(days=6)
        elif budget.period_type == BudgetPeriodType.MONTHLY:
            start = ref.replace(day=1)
            if ref.month == 12:
                end = date(ref.year + 1, 1, 1) - timedelta(days=1)
            else:
                end = date(ref.year, ref.month + 1, 1) - timedelta(days=1)
        else:
            start = date(ref.year, 1, 1)
            end = date(ref.year, 12, 31)
        if budget.start_date and start < budget.start_date:
            start = budget.start_date
        if budget.end_date and end > budget.end_date:
            end = budget.end_date
        return (start, end)

    async def create(self, user: User, data: BudgetCreate, ip: str | None = None) -> Budget:
        category = await self.category_repo.get_by_id_for_user(UUID(data.category_id), user.id)
        if category is None:
            raise NotFoundError("Category not found")
        budget = Budget(
            user_id=user.id,
            category_id=category.id,
            amount_limit=data.amount_limit,
            period_type=data.period_type,
            start_date=data.start_date,
            end_date=data.end_date,
            rollover_enabled=data.rollover_enabled,
        )
        await self.repo.create(budget)
        await self.audit.log(
            "create", "budget", user_id=user.id, entity_id=budget.id, ip_address=ip
        )
        return budget

    async def get_status(self, user_id: UUID, budget_id: UUID) -> BudgetStatusResponse:
        budget = await self.repo.get_by_id_for_user(budget_id, user_id)
        if budget is None:
            raise NotFoundError("Budget not found")
        start, end = self._period_bounds(budget)
        spent_val = await self.tx_repo.sum_by_category(
            user_id, budget.category_id, start, end, TransactionType.EXPENSE
        )
        spent = Decimal(str(spent_val))
        remaining = budget.amount_limit - spent
        percent = float(spent / budget.amount_limit * 100) if budget.amount_limit else 0.0
        today = date.today()
        days_elapsed = max((min(today, end) - start).days + 1, 1)
        avg_daily = spent / days_elapsed if days_elapsed > 0 else Decimal("0")
        days_until_exceed: int | None = None
        if avg_daily > 0 and remaining > 0:
            days_until_exceed = int(remaining / avg_daily)
        elif remaining <= 0:
            days_until_exceed = 0
        return BudgetStatusResponse(
            budget_id=str(budget.id),
            spent=spent,
            remaining=remaining,
            percent_used=percent,
            days_until_exceed=days_until_exceed,
            is_exceeded=spent > budget.amount_limit,
        )

    async def check_all_budgets(self) -> None:
        today = date.today()
        stmt = select(Budget).where(
            Budget.start_date <= today, Budget.end_date.is_(None) | (Budget.end_date >= today)
        )
        result = await self.session.execute(stmt)
        budgets = list(result.scalars().all())
        for budget in budgets:
            status = await self.get_status(budget.user_id, budget.id)
            if status.is_exceeded:
                await self.notifications.notify_budget_exceeded(budget.user_id, budget, status)
            elif status.percent_used >= settings.budget_warning_threshold * 100:
                await self.notifications.notify_budget_warning(budget.user_id, budget, status)

    async def update(
        self, user_id: UUID, budget_id: UUID, data: BudgetUpdate, ip: str | None = None
    ) -> Budget:
        budget = await self.repo.get_by_id_for_user(budget_id, user_id)
        if budget is None:
            raise NotFoundError("Budget not found")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(budget, field, value)
        await self.session.flush()
        await self.audit.log(
            "update", "budget", user_id=user_id, entity_id=budget.id, ip_address=ip
        )
        return budget

    async def delete(self, user_id: UUID, budget_id: UUID, ip: str | None = None) -> None:
        budget = await self.repo.get_by_id_for_user(budget_id, user_id)
        if budget is None:
            raise NotFoundError("Budget not found")
        await self.session.delete(budget)
        await self.session.flush()
        await self.audit.log(
            "delete", "budget", user_id=user_id, entity_id=budget_id, ip_address=ip
        )
