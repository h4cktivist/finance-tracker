import uuid
from decimal import Decimal

from sqlalchemy import JSON, CheckConstraint, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.enums import pg_enum
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.transaction import TransactionType


class TransactionTemplate(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "transaction_templates"
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    target_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    card_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cards.id", ondelete="SET NULL"), nullable=True
    )
    type: Mapped[TransactionType] = mapped_column(
        pg_enum(TransactionType, "transaction_type"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    merchant_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    tag_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transaction_templates_amount_positive"),
    )
