from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.notification import Notification, NotificationType
from app.repositories.notification import NotificationRepository

if TYPE_CHECKING:
    from app.models.budget import Budget
    from app.models.card import Card
    from app.models.cashback import CashbackAccrual
    from app.models.financial_goal import FinancialGoal
    from app.models.recurring import RecurringTransaction
    from app.schemas.budget import BudgetStatusResponse


class NotificationService:

    def __init__(self, session: AsyncSession) -> None:
        self.repo = NotificationRepository(session)

    async def _create(
        self,
        user_id: UUID,
        type_: NotificationType,
        title: str,
        body: str,
        payload: dict[str, Any] | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id, type=type_, title=title, body=body, payload=payload
        )
        return await self.repo.create(notification)

    async def notify_budget_warning(
        self, user_id: UUID, budget: Budget, status: BudgetStatusResponse
    ) -> None:
        await self._create(
            user_id,
            NotificationType.BUDGET_WARNING,
            "Budget warning",
            f"You have used {status.percent_used:.0f}% of your budget.",
            {"budget_id": str(budget.id), "percent_used": status.percent_used},
        )

    async def notify_budget_exceeded(
        self, user_id: UUID, budget: Budget, status: BudgetStatusResponse
    ) -> None:
        await self._create(
            user_id,
            NotificationType.BUDGET_EXCEEDED,
            "Budget exceeded",
            f"Budget exceeded by {abs(status.remaining)}.",
            {"budget_id": str(budget.id), "overspent": str(abs(status.remaining))},
        )

    async def notify_recurring_created(
        self, user_id: UUID, recurring: RecurringTransaction
    ) -> None:
        await self._create(
            user_id,
            NotificationType.RECURRING_CREATED,
            "Recurring transaction created",
            f"Created transaction from recurring rule: {recurring.description or recurring.id}",
            {"recurring_id": str(recurring.id)},
        )

    async def notify_goal_deadline(self, user_id: UUID, goal: FinancialGoal) -> None:
        await self._create(
            user_id,
            NotificationType.GOAL_DEADLINE,
            "Goal deadline approaching",
            f"Goal '{goal.name}' deadline is on {goal.deadline}.",
            {"goal_id": str(goal.id)},
        )

    async def notify_cashback_available(
        self, user_id: UUID, accrual: CashbackAccrual, card: Card
    ) -> None:
        await self._create(
            user_id,
            NotificationType.CASHBACK_AVAILABLE,
            "Cashback earned",
            f"You earned {accrual.amount} cashback on card {card.name}.",
            {"accrual_id": str(accrual.id), "card_id": str(card.id)},
        )

    async def list(
        self, user_id: UUID, page: int, page_size: int, unread_only: bool
    ) -> tuple[list[Notification], int]:
        return await self.repo.list_by_user(
            user_id, page=page, page_size=page_size, unread_only=unread_only
        )

    async def mark_read(self, user_id: UUID, notification_id: UUID) -> Notification:
        notification = await self.repo.get_by_id_for_user(notification_id, user_id)
        if notification is None:
            raise NotFoundError("Notification not found")
        return await self.repo.mark_read(notification)

    async def mark_all_read(self, user_id: UUID) -> int:
        return await self.repo.mark_all_read(user_id)
