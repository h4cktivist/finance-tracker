from datetime import date
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import TransactionTag
from app.models.transaction import Transaction, TransactionType
from app.repositories.base import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Transaction)

    def _base_query(self, user_id: UUID):
        return select(Transaction).where(
            Transaction.user_id == user_id, Transaction.deleted_at.is_(None)
        )

    async def get_by_id_for_user(self, transaction_id: UUID, user_id: UUID) -> Transaction | None:
        result = await self.session.execute(
            self._base_query(user_id).where(Transaction.id == transaction_id)
        )
        return result.scalar_one_or_none()

    async def list_filtered(
        self,
        user_id: UUID,
        *,
        page: int = 1,
        page_size: int = 20,
        type_filter: TransactionType | None = None,
        account_id: UUID | None = None,
        category_id: UUID | None = None,
        tag_id: UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        search: str | None = None,
        sort_by: str = "transaction_date",
        sort_order: str = "desc",
    ) -> tuple[list[Transaction], int]:
        stmt = self._base_query(user_id)
        if type_filter:
            stmt = stmt.where(Transaction.type == type_filter)
        if account_id:
            stmt = stmt.where(Transaction.account_id == account_id)
        if category_id:
            stmt = stmt.where(Transaction.category_id == category_id)
        if tag_id:
            stmt = stmt.join(TransactionTag).where(TransactionTag.tag_id == tag_id)
        if date_from:
            stmt = stmt.where(Transaction.transaction_date >= date_from)
        if date_to:
            stmt = stmt.where(Transaction.transaction_date <= date_to)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Transaction.description.ilike(pattern), Transaction.merchant_name.ilike(pattern)
                )
            )
        sort_col = getattr(Transaction, sort_by, Transaction.transaction_date)
        stmt = stmt.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())
        count_result = await self.session.execute(select(func.count()).select_from(stmt.subquery()))
        total = count_result.scalar_one()
        offset = (page - 1) * page_size
        result = await self.session.execute(stmt.offset(offset).limit(page_size))
        return (list(result.scalars().all()), total)

    async def sum_by_category(
        self,
        user_id: UUID,
        category_id: UUID,
        date_from: date,
        date_to: date,
        tx_type: TransactionType,
    ) -> float:
        result = await self.session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.user_id == user_id,
                Transaction.category_id == category_id,
                Transaction.type == tx_type,
                Transaction.transaction_date >= date_from,
                Transaction.transaction_date <= date_to,
                Transaction.deleted_at.is_(None),
            )
        )
        return float(result.scalar_one())
