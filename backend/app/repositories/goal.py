from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.financial_goal import FinancialGoal, GoalStatus
from app.repositories.base import BaseRepository


class GoalRepository(BaseRepository[FinancialGoal]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, FinancialGoal)

    async def list_by_user(self, user_id: UUID) -> list[FinancialGoal]:
        result = await self.session.execute(
            select(FinancialGoal)
            .where(FinancialGoal.user_id == user_id)
            .order_by(FinancialGoal.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id_for_user(self, goal_id: UUID, user_id: UUID) -> FinancialGoal | None:
        result = await self.session.execute(
            select(FinancialGoal).where(
                FinancialGoal.id == goal_id, FinancialGoal.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def list_active_with_deadline(self, days_ahead: int) -> list[FinancialGoal]:
        from datetime import date, timedelta

        target = date.today() + timedelta(days=days_ahead)
        result = await self.session.execute(
            select(FinancialGoal).where(
                FinancialGoal.status == GoalStatus.ACTIVE,
                FinancialGoal.deadline.isnot(None),
                FinancialGoal.deadline <= target,
                FinancialGoal.deadline >= date.today(),
            )
        )
        return list(result.scalars().all())
