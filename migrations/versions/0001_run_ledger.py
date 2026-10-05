"""run_ledger: append-only hash-chained audit trail (T-104).

Revision ID: 0001_run_ledger
Revises:
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_run_ledger"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS itp")
    op.create_table(
        "run_ledger",
        sa.Column("run_id", sa.Uuid(), primary_key=True),
        sa.Column("seq", sa.Integer(), primary_key=True),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("body", postgresql.JSONB(), nullable=False),
        sa.Column("prev_hash", sa.String(64)),
        sa.Column("hash", sa.String(64), nullable=False),
        sa.Column("trace_id", sa.String(), nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("seq >= 1", name="run_ledger_seq_positive"),
        schema="itp",
    )
    # Append-only: refuse UPDATE, DELETE and TRUNCATE (Persistence sheet: 10 years, append-only).
    op.execute(
        """
        CREATE FUNCTION itp.run_ledger_append_only() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'itp.run_ledger is append-only';
        END
        $$
        """
    )
    op.execute(
        "CREATE TRIGGER run_ledger_no_update_delete BEFORE UPDATE OR DELETE ON itp.run_ledger "
        "FOR EACH ROW EXECUTE FUNCTION itp.run_ledger_append_only()"
    )
    op.execute(
        "CREATE TRIGGER run_ledger_no_truncate BEFORE TRUNCATE ON itp.run_ledger "
        "FOR EACH STATEMENT EXECUTE FUNCTION itp.run_ledger_append_only()"
    )


def downgrade() -> None:
    op.drop_table("run_ledger", schema="itp")
    op.execute("DROP FUNCTION itp.run_ledger_append_only()")
