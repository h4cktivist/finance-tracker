from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cashback import CashbackAccrual, CashbackAccrualStatus
from app.repositories.base import BaseRepository


class CashbackAccrualRepository(BaseRepository[CashbackAccrual]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, CashbackAccrual)

    async def monthly_total_for_card_category(
        self, card_id: UUID, category_id: UUID, period_month: str
    ) -> Decimal:
        result = await self.session.execute(
            select(func.coalesce(func.sum(CashbackAccrual.amount), 0)).where(
                CashbackAccrual.card_id == card_id,
                CashbackAccrual.period_month == period_month,
                CashbackAccrual.status == CashbackAccrualStatus.ACCRUED,
            )
        )
        return Decimal(str(result.scalar_one()))

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
