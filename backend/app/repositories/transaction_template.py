from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction_template import TransactionTemplate
from app.repositories.base import BaseRepository


class TransactionTemplateRepository(BaseRepository[TransactionTemplate]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, TransactionTemplate)

    async def list_by_user(self, user_id: UUID) -> list[TransactionTemplate]:
        result = await self.session.execute(
            select(TransactionTemplate)
            .where(TransactionTemplate.user_id == user_id)
            .order_by(TransactionTemplate.name)
        )
        return list(result.scalars().all())

    async def get_by_id_for_user(
        self, template_id: UUID, user_id: UUID
    ) -> TransactionTemplate | None:
        result = await self.session.execute(
            select(TransactionTemplate).where(
                TransactionTemplate.id == template_id, TransactionTemplate.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def delete(self, template: TransactionTemplate) -> None:
        await self.session.delete(template)
        await self.session.flush()
