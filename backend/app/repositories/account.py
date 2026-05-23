from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.repositories.base import BaseRepository


class AccountRepository(BaseRepository[Account]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Account)

    async def list_by_user(self, user_id: UUID, include_deleted: bool = False) -> list[Account]:
        stmt = select(Account).where(Account.user_id == user_id)
        if not include_deleted:
            stmt = stmt.where(Account.deleted_at.is_(None))
        result = await self.session.execute(stmt.order_by(Account.created_at.desc()))
        return list(result.scalars().all())

    async def get_by_id_for_user(self, account_id: UUID, user_id: UUID) -> Account | None:
        result = await self.session.execute(
            select(Account).where(
                Account.id == account_id, Account.user_id == user_id, Account.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()
