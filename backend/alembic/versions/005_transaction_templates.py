from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "transaction_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accounts.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "card_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cards.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "type",
            postgresql.ENUM(name="transaction_type", create_type=False),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("merchant_name", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("tag_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("amount > 0", name="ck_transaction_templates_amount_positive"),
    )
    op.create_index("ix_transaction_templates_user_id", "transaction_templates", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_transaction_templates_user_id", table_name="transaction_templates")
    op.drop_table("transaction_templates")
