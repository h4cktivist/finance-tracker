import uuid
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import pg_enum
from app.db.mixins import UUIDPrimaryKeyMixin


class LedgerSide(StrEnum):
    DEBIT = "debit"
    CREDIT = "credit"


class LedgerEntry(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "ledger_entries"
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    side: Mapped[LedgerSide] = mapped_column(pg_enum(LedgerSide, "ledger_side"), nullable=False)
    transaction: Mapped["Transaction"] = relationship(back_populates="ledger_entries")
    account: Mapped["Account"] = relationship(back_populates="ledger_entries")
    __table_args__ = (CheckConstraint("amount > 0", name="ck_ledger_entries_amount_positive"),)
