from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.models.financial_goal import FinancialGoal, GoalStatus
from app.models.user import User
from app.repositories.account import AccountRepository
from app.repositories.goal import GoalRepository
from app.repositories.ledger import LedgerRepository
from app.schemas.goal import GoalCreate, GoalProgressResponse, GoalUpdate
from app.services.audit import AuditService
from app.services.notification import NotificationService

settings = get_settings()


class GoalService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = GoalRepository(session)
        self.account_repo = AccountRepository(session)
        self.ledger_repo = LedgerRepository(session)
        self.audit = AuditService(session)
        self.notifications = NotificationService(session)

    async def create(self, user: User, data: GoalCreate, ip: str | None = None) -> FinancialGoal:
        goal = FinancialGoal(
            user_id=user.id,
            name=data.name,
            target_amount=data.target_amount,
            deadline=data.deadline,
            linked_account_id=UUID(data.linked_account_id) if data.linked_account_id else None,
        )
        if goal.linked_account_id:
            account = await self.account_repo.get_by_id_for_user(goal.linked_account_id, user.id)
            if account:
                goal.current_amount = await self.ledger_repo.get_account_balance(
                    account.id, account.initial_balance
                )
        await self.repo.create(goal)
        await self.audit.log("create", "goal", user_id=user.id, entity_id=goal.id, ip_address=ip)
        return goal

    async def sync_progress(self, goal: FinancialGoal) -> FinancialGoal:
        if goal.status != GoalStatus.ACTIVE or not goal.linked_account_id:
            return goal
        account = await self.account_repo.get_by_id_for_user(goal.linked_account_id, goal.user_id)
        if account is None:
            return goal
        new_amount = await self.ledger_repo.get_account_balance(account.id, account.initial_balance)
        if new_amount == goal.current_amount:
            return goal
        goal.current_amount = new_amount
        if new_amount >= goal.target_amount:
            goal.status = GoalStatus.COMPLETED
        await self.session.flush()
        return goal

    async def get_progress(self, user_id: UUID, goal_id: UUID) -> GoalProgressResponse:
        goal = await self.repo.get_by_id_for_user(goal_id, user_id)
        if goal is None:
            raise NotFoundError("Goal not found")
        goal = await self.sync_progress(goal)
        progress = (
            float(goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0.0
        )
        return GoalProgressResponse(
            goal_id=str(goal.id),
            current_amount=goal.current_amount,
            target_amount=goal.target_amount,
            progress_percent=progress,
            remaining=max(goal.target_amount - goal.current_amount, Decimal("0")),
            status=goal.status,
        )

    async def list_by_user_with_sync(self, user_id: UUID) -> list[FinancialGoal]:
        """
        Returns goals with `current_amount` synchronized to the linked account balance.
        """
        goals = await self.repo.list_by_user(user_id)
        for goal in goals:
            await self.sync_progress(goal)
        return goals

    async def check_deadlines(self) -> None:
        goals = await self.repo.list_active_with_deadline(settings.goal_deadline_warning_days)
        for goal in goals:
            await self.notifications.notify_goal_deadline(goal.user_id, goal)

    async def update(
        self, user_id: UUID, goal_id: UUID, data: GoalUpdate, ip: str | None = None
    ) -> FinancialGoal:
        goal = await self.repo.get_by_id_for_user(goal_id, user_id)
        if goal is None:
            raise NotFoundError("Goal not found")
        if data.name is not None:
            goal.name = data.name
        if data.target_amount is not None:
            goal.target_amount = data.target_amount
        if data.deadline is not None:
            goal.deadline = data.deadline
        if data.status is not None:
            goal.status = data.status
        await self.session.flush()
        await self.audit.log("update", "goal", user_id=user_id, entity_id=goal.id, ip_address=ip)
        return goal

    async def delete(self, user_id: UUID, goal_id: UUID, ip: str | None = None) -> None:
        goal = await self.repo.get_by_id_for_user(goal_id, user_id)
        if goal is None:
            raise NotFoundError("Goal not found")
        await self.session.delete(goal)
        await self.session.flush()
        await self.audit.log("delete", "goal", user_id=user_id, entity_id=goal_id, ip_address=ip)
