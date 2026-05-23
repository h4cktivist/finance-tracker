from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
CHECK_TRANSFER_BALANCE_FN = "\nCREATE OR REPLACE FUNCTION check_transfer_balance() RETURNS TRIGGER AS $$\nDECLARE\n    tg_id UUID;\n    debit_sum NUMERIC;\n    credit_sum NUMERIC;\nBEGIN\n    IF TG_OP = 'DELETE' THEN\n        SELECT t.transfer_group_id INTO tg_id\n        FROM transactions t\n        WHERE t.id = OLD.transaction_id;\n    ELSE\n        SELECT t.transfer_group_id INTO tg_id\n        FROM transactions t\n        WHERE t.id = NEW.transaction_id;\n    END IF;\n\n    IF tg_id IS NULL THEN\n        RETURN COALESCE(NEW, OLD);\n    END IF;\n\n    SELECT\n        COALESCE(SUM(CASE WHEN le.side = 'debit'  THEN le.amount ELSE 0 END), 0),\n        COALESCE(SUM(CASE WHEN le.side = 'credit' THEN le.amount ELSE 0 END), 0)\n    INTO debit_sum, credit_sum\n    FROM ledger_entries le\n    JOIN transactions t ON t.id = le.transaction_id\n    WHERE t.transfer_group_id = tg_id\n      AND t.deleted_at IS NULL;\n\n    IF debit_sum <> credit_sum THEN\n        RAISE EXCEPTION\n            'Transfer group % is unbalanced: debits=%, credits=%',\n            tg_id, debit_sum, credit_sum;\n    END IF;\n\n    RETURN COALESCE(NEW, OLD);\nEND;\n$$ LANGUAGE plpgsql;\n"
CREATE_TRANSFER_BALANCE_TRIGGER = "\nCREATE CONSTRAINT TRIGGER check_transfer_balance_trigger\nAFTER INSERT OR UPDATE OR DELETE ON ledger_entries\nDEFERRABLE INITIALLY DEFERRED\nFOR EACH ROW EXECUTE FUNCTION check_transfer_balance();\n"


def upgrade() -> None:
    op.drop_column("accounts", "currency")
    op.drop_column("transactions", "currency")
    op.drop_column("recurring_transactions", "currency")
    op.create_check_constraint("ck_ledger_entries_amount_positive", "ledger_entries", "amount > 0")
    op.create_check_constraint("ck_transactions_amount_positive", "transactions", "amount > 0")
    op.create_check_constraint(
        "ck_recurring_transactions_amount_positive", "recurring_transactions", "amount > 0"
    )
    op.create_check_constraint(
        "ck_recurring_transactions_interval_positive", "recurring_transactions", "interval >= 1"
    )
    op.drop_constraint("uq_tags_user_name", "tags", type_="unique")
    op.create_index(
        "uq_tags_user_name_active",
        "tags",
        ["user_id", "name"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.execute(CHECK_TRANSFER_BALANCE_FN)
    op.execute(CREATE_TRANSFER_BALANCE_TRIGGER)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS check_transfer_balance_trigger ON ledger_entries")
    op.execute("DROP FUNCTION IF EXISTS check_transfer_balance()")
    op.drop_index("uq_tags_user_name_active", table_name="tags")
    op.create_unique_constraint("uq_tags_user_name", "tags", ["user_id", "name"])
    op.drop_constraint(
        "ck_recurring_transactions_interval_positive", "recurring_transactions", type_="check"
    )
    op.drop_constraint(
        "ck_recurring_transactions_amount_positive", "recurring_transactions", type_="check"
    )
    op.drop_constraint("ck_transactions_amount_positive", "transactions", type_="check")
    op.drop_constraint("ck_ledger_entries_amount_positive", "ledger_entries", type_="check")
    op.add_column(
        "recurring_transactions",
        sa.Column("currency", sa.String(3), nullable=False, server_default="RUB"),
    )
    op.add_column(
        "transactions", sa.Column("currency", sa.String(3), nullable=False, server_default="RUB")
    )
    op.add_column(
        "accounts", sa.Column("currency", sa.String(3), nullable=False, server_default="RUB")
    )
