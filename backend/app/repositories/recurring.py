from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recurring import RecurringTransaction
from app.models.recurring_execution import RecurringExecution
from app.repositories.base import BaseRepository


class RecurringRepository(BaseRepository[RecurringTransaction]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, RecurringTransaction)

    async def list_by_user(self, user_id: UUID) -> list[RecurringTransaction]:
        result = await self.session.execute(
            select(RecurringTransaction)
            .where(RecurringTransaction.user_id == user_id)
            .order_by(RecurringTransaction.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id_for_user(
        self, recurring_id: UUID, user_id: UUID
    ) -> RecurringTransaction | None:
        result = await self.session.execute(
            select(RecurringTransaction).where(
                RecurringTransaction.id == recurring_id, RecurringTransaction.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def list_due(self, as_of: date) -> list[RecurringTransaction]:
        result = await self.session.execute(
            select(RecurringTransaction).where(
                RecurringTransaction.is_active.is_(True),
                RecurringTransaction.next_execution_date <= as_of,
            )
        )
        return list(result.scalars().all())


class RecurringExecutionRepository(BaseRepository[RecurringExecution]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, RecurringExecution)

    async def exists(self, recurring_id: UUID, execution_date: date) -> bool:
        result = await self.session.execute(
            select(RecurringExecution).where(
                RecurringExecution.recurring_id == recurring_id,
                RecurringExecution.execution_date == execution_date,
            )
        )
        return result.scalar_one_or_none() is not None
