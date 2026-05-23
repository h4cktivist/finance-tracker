from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget
from app.repositories.base import BaseRepository


class BudgetRepository(BaseRepository[Budget]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Budget)

    async def list_by_user(self, user_id: UUID) -> list[Budget]:
        result = await self.session.execute(
            select(Budget).where(Budget.user_id == user_id).order_by(Budget.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id_for_user(self, budget_id: UUID, user_id: UUID) -> Budget | None:
        result = await self.session.execute(
            select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id)
        )
        return result.scalar_one_or_none()
