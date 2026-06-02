from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cashback import CashbackAccrual, CashbackAccrualStatus
from app.models.transaction import Transaction
from app.repositories.base import BaseRepository


class CashbackAccrualRepository(BaseRepository[CashbackAccrual]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, CashbackAccrual)

    async def monthly_total_for_card_category(
        self, card_id: UUID, category_id: UUID, period_month: str
    ) -> Decimal:
        result = await self.session.execute(
            select(func.coalesce(func.sum(CashbackAccrual.amount), 0))
            .select_from(CashbackAccrual)
            .join(Transaction, CashbackAccrual.transaction_id == Transaction.id)
            .where(
                CashbackAccrual.card_id == card_id,
                CashbackAccrual.period_month == period_month,
                CashbackAccrual.status == CashbackAccrualStatus.ACCRUED,
                Transaction.category_id == category_id,
            )
        )
        return Decimal(str(result.scalar_one()))

    async def sum_accrued_by_transaction_ids(
        self, transaction_ids: list[UUID]
    ) -> dict[UUID, Decimal]:
        if not transaction_ids:
            return {}
        result = await self.session.execute(
            select(
                CashbackAccrual.transaction_id,
                func.coalesce(func.sum(CashbackAccrual.amount), 0),
            )
            .where(
                CashbackAccrual.transaction_id.in_(transaction_ids),
                CashbackAccrual.status == CashbackAccrualStatus.ACCRUED,
            )
            .group_by(CashbackAccrual.transaction_id)
        )
        return {row[0]: Decimal(str(row[1])) for row in result.all()}

    async def delete_for_card_transactions(
        self, card_id: UUID, transaction_ids: list[UUID]
    ) -> None:
        if not transaction_ids:
            return
        await self.session.execute(
            delete(CashbackAccrual).where(
                CashbackAccrual.card_id == card_id,
                CashbackAccrual.transaction_id.in_(transaction_ids),
            )
        )

    async def list_by_user(
        self, user_id: UUID, status: CashbackAccrualStatus | None = None
    ) -> list[CashbackAccrual]:
        stmt = select(CashbackAccrual).where(CashbackAccrual.user_id == user_id)
        if status:
            stmt = stmt.where(CashbackAccrual.status == status)
        result = await self.session.execute(stmt.order_by(CashbackAccrual.period_month.desc()))
        return list(result.scalars().all())

    async def total_earned(self, user_id: UUID, period_month: str | None = None) -> Decimal:
        stmt = select(func.coalesce(func.sum(CashbackAccrual.amount), 0)).where(
            CashbackAccrual.user_id == user_id,
            CashbackAccrual.status == CashbackAccrualStatus.ACCRUED,
        )
        if period_month:
            stmt = stmt.where(CashbackAccrual.period_month == period_month)
        result = await self.session.execute(stmt)
        return Decimal(str(result.scalar_one()))
