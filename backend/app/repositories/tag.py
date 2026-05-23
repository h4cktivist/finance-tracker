from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag, TransactionTag
from app.repositories.base import BaseRepository


class TagRepository(BaseRepository[Tag]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Tag)

    async def list_by_user(self, user_id: UUID) -> list[Tag]:
        result = await self.session.execute(
            select(Tag).where(Tag.user_id == user_id, Tag.deleted_at.is_(None)).order_by(Tag.name)
        )
        return list(result.scalars().all())

    async def get_by_id_for_user(self, tag_id: UUID, user_id: UUID) -> Tag | None:
        result = await self.session.execute(
            select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id, Tag.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def set_transaction_tags(self, transaction_id: UUID, tag_ids: list[UUID]) -> None:
        await self.session.execute(
            delete(TransactionTag).where(TransactionTag.transaction_id == transaction_id)
        )
        for tag_id in tag_ids:
            self.session.add(TransactionTag(transaction_id=transaction_id, tag_id=tag_id))
        await self.session.flush()

    async def get_transaction_tag_ids(self, transaction_id: UUID) -> list[UUID]:
        result = await self.session.execute(
            select(TransactionTag.tag_id).where(TransactionTag.transaction_id == transaction_id)
        )
        return list(result.scalars().all())
