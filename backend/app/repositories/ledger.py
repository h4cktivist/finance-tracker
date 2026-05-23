from decimal import Decimal
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ledger import LedgerEntry, LedgerSide
from app.models.transaction import Transaction
from app.repositories.base import BaseRepository


class LedgerRepository(BaseRepository[LedgerEntry]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, LedgerEntry)

    async def get_account_balance(self, account_id: UUID, initial_balance: Decimal) -> Decimal:
        result = await self.session.execute(
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (LedgerEntry.side == LedgerSide.CREDIT, LedgerEntry.amount),
                            else_=-LedgerEntry.amount,
                        )
                    ),
                    0,
                )
            )
            .join(Transaction, LedgerEntry.transaction_id == Transaction.id)
            .where(LedgerEntry.account_id == account_id, Transaction.deleted_at.is_(None))
        )
        ledger_sum = result.scalar_one()
        return initial_balance + Decimal(str(ledger_sum))

    async def get_total_balance_for_user(self, account_balances: dict[UUID, Decimal]) -> Decimal:
        return sum(account_balances.values(), Decimal("0"))
