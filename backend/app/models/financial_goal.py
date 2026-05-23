import uuid
from datetime import date
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.enums import pg_enum
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class GoalStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FinancialGoal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "financial_goals"
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    current_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0"), nullable=False
    )
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    linked_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[GoalStatus] = mapped_column(
        pg_enum(GoalStatus, "goal_status"), default=GoalStatus.ACTIVE, nullable=False
    )
