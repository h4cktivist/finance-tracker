from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cashback_payouts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "card_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cards.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "transaction_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("transactions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("period_month", sa.String(7), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("card_id", "period_month", name="uq_cashback_payout_card_period"),
    )
    op.create_index("ix_cashback_payouts_user_id", "cashback_payouts", ["user_id"])
    op.create_index("ix_cashback_payouts_card_id", "cashback_payouts", ["card_id"])
    op.create_index("ix_cashback_payouts_period_month", "cashback_payouts", ["period_month"])


def downgrade() -> None:
    op.drop_index("ix_cashback_payouts_period_month", table_name="cashback_payouts")
    op.drop_index("ix_cashback_payouts_card_id", table_name="cashback_payouts")
    op.drop_index("ix_cashback_payouts_user_id", table_name="cashback_payouts")
    op.drop_table("cashback_payouts")
