from decimal import Decimal
from uuid import UUID

from sqlalchemy import case, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cashback import CashbackAccrual, CashbackAccrualStatus, CashbackPayout
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
        info = await self.accrued_info_by_transaction_ids(transaction_ids)
        return {tx_id: amount for tx_id, (amount, _) in info.items()}

    async def accrued_info_by_transaction_ids(
        self, transaction_ids: list[UUID]
    ) -> dict[UUID, tuple[Decimal, bool]]:
        if not transaction_ids:
            return {}
        result = await self.session.execute(
            select(
                CashbackAccrual.transaction_id,
                func.coalesce(func.sum(CashbackAccrual.amount), 0),
                func.max(
                    case((CashbackAccrual.rule_id.is_(None), 1), else_=0)
                ),
            )
            .where(
                CashbackAccrual.transaction_id.in_(transaction_ids),
                CashbackAccrual.status == CashbackAccrualStatus.ACCRUED,
            )
            .group_by(CashbackAccrual.transaction_id)
        )
        return {
            row[0]: (Decimal(str(row[1])), bool(row[2]))
            for row in result.all()
        }

    async def get_for_transaction_card(
        self, transaction_id: UUID, card_id: UUID
    ) -> CashbackAccrual | None:
        result = await self.session.execute(
            select(CashbackAccrual).where(
                CashbackAccrual.transaction_id == transaction_id,
                CashbackAccrual.card_id == card_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete_for_transaction(self, transaction_id: UUID, user_id: UUID) -> None:
        await self.session.execute(
            delete(CashbackAccrual).where(
                CashbackAccrual.transaction_id == transaction_id,
                CashbackAccrual.user_id == user_id,
            )
        )

    async def delete_for_card_transactions(
        self, card_id: UUID, transaction_ids: list[UUID], *, auto_only: bool = False
    ) -> None:
        if not transaction_ids:
            return
        stmt = delete(CashbackAccrual).where(
            CashbackAccrual.card_id == card_id,
            CashbackAccrual.transaction_id.in_(transaction_ids),
        )
        if auto_only:
            stmt = stmt.where(CashbackAccrual.rule_id.isnot(None))
        await self.session.execute(stmt)

    async def list_by_user(
        self, user_id: UUID, status: CashbackAccrualStatus | None = None
    ) -> list[CashbackAccrual]:
        stmt = select(CashbackAccrual).where(CashbackAccrual.user_id == user_id)
        if status:
            stmt = stmt.where(CashbackAccrual.status == status)
        result = await self.session.execute(stmt.order_by(CashbackAccrual.period_month.desc()))
        return list(result.scalars().all())

    async def earned_by_month(self, user_id: UUID, year: int) -> list[tuple[str, Decimal]]:
        result = await self.session.execute(
            select(CashbackAccrual.period_month, func.coalesce(func.sum(CashbackAccrual.amount), 0))
            .where(
                CashbackAccrual.user_id == user_id,
                CashbackAccrual.status == CashbackAccrualStatus.ACCRUED,
                CashbackAccrual.period_month.like(f"{year}-%"),
            )
            .group_by(CashbackAccrual.period_month)
            .order_by(CashbackAccrual.period_month)
        )
        return [(row[0], Decimal(str(row[1]))) for row in result.all()]

    async def total_earned(self, user_id: UUID, period_month: str | None = None) -> Decimal:
        stmt = select(func.coalesce(func.sum(CashbackAccrual.amount), 0)).where(
            CashbackAccrual.user_id == user_id,
            CashbackAccrual.status == CashbackAccrualStatus.ACCRUED,
        )
        if period_month:
            stmt = stmt.where(CashbackAccrual.period_month == period_month)
        result = await self.session.execute(stmt)
        return Decimal(str(result.scalar_one()))

    async def earned_by_card(self, user_id: UUID, period_month: str) -> dict[UUID, Decimal]:
        result = await self.session.execute(
            select(CashbackAccrual.card_id, func.coalesce(func.sum(CashbackAccrual.amount), 0))
            .where(
                CashbackAccrual.user_id == user_id,
                CashbackAccrual.status == CashbackAccrualStatus.ACCRUED,
                CashbackAccrual.period_month == period_month,
            )
            .group_by(CashbackAccrual.card_id)
        )
        return {row[0]: Decimal(str(row[1])) for row in result.all()}


class CashbackPayoutRepository(BaseRepository[CashbackPayout]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, CashbackPayout)

    async def get_for_card_period(
        self, card_id: UUID, period_month: str
    ) -> CashbackPayout | None:
        result = await self.session.execute(
            select(CashbackPayout).where(
                CashbackPayout.card_id == card_id,
                CashbackPayout.period_month == period_month,
            )
        )
        return result.scalar_one_or_none()

    async def list_paid_card_ids(self, user_id: UUID, period_month: str) -> set[UUID]:
        """Карты с уже выплаченным кэшбэком за период (удалённые транзакции не считаются)."""
        result = await self.session.execute(
            select(CashbackPayout.card_id)
            .join(Transaction, CashbackPayout.transaction_id == Transaction.id)
            .where(
                CashbackPayout.user_id == user_id,
                CashbackPayout.period_month == period_month,
                Transaction.deleted_at.is_(None),
            )
        )
        return set(result.scalars().all())

    async def delete(self, payout: CashbackPayout) -> None:
        await self.session.delete(payout)
        await self.session.flush()
