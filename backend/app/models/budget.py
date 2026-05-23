import uuid
from datetime import date
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Boolean, Date, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.enums import pg_enum
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class BudgetPeriodType(StrEnum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class Budget(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "budgets"
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    amount_limit: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    period_type: Mapped[BudgetPeriodType] = mapped_column(
        pg_enum(BudgetPeriodType, "budget_period_type"), nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    rollover_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
