import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import UUIDPrimaryKeyMixin


class RecurringExecution(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "recurring_executions"
    recurring_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recurring_transactions.id", ondelete="CASCADE"),
        nullable=False,
    )
    execution_date: Mapped[date] = mapped_column(Date, nullable=False)
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    __table_args__ = (
        UniqueConstraint("recurring_id", "execution_date", name="uq_recurring_execution_date"),
    )
