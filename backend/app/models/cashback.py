import uuid
from datetime import date
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import pg_enum
from app.db.mixins import UUIDPrimaryKeyMixin


class CashbackAccrualStatus(StrEnum):
    ACCRUED = "accrued"
    MISSED = "missed"


class CashbackRule(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "cashback_rules"
    card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cards.id", ondelete="CASCADE"), index=True, nullable=False
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    cashback_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    monthly_limit: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    min_purchase_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    card: Mapped["Card"] = relationship(back_populates="cashback_rules")


class CashbackAccrual(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "cashback_accruals"
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False
    )
    card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cards.id", ondelete="CASCADE"), nullable=False
    )
    rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cashback_rules.id", ondelete="SET NULL"), nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    period_month: Mapped[str] = mapped_column(String(7), index=True, nullable=False)
    status: Mapped[CashbackAccrualStatus] = mapped_column(
        pg_enum(CashbackAccrualStatus, "cashback_accrual_status"), nullable=False
    )
    __table_args__ = (
        UniqueConstraint("transaction_id", "card_id", name="uq_cashback_accrual_tx_card"),
    )
