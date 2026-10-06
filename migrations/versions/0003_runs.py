"""runs: one row per run (T-108).

Revision ID: 0003_runs
Revises: 0002_file_records
Create Date: 2026-10-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_runs"
down_revision: str | None = "0002_file_records"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TERMINALS = ("Succeeded", "Failed", "Stopped", "Abandoned", "Held", "Rejected")


def upgrade() -> None:
    terminals = ", ".join(f"'{t}'" for t in TERMINALS)
    op.create_table(
        "runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("entity", sa.String(), nullable=False),
        sa.Column("thread_id", sa.String(), nullable=False),
        sa.Column("goal_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("terminal", sa.String()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("thread_id", name="runs_thread_id_key"),
        sa.CheckConstraint(
            "status IN ('running', 'paused', 'finished')", name="runs_status_values"
        ),
        sa.CheckConstraint(
            f"terminal IS NULL OR terminal IN ({terminals})", name="runs_terminal_values"
        ),
        sa.CheckConstraint(
            "(status = 'finished') = (terminal IS NOT NULL)", name="runs_terminal_iff_finished"
        ),
        sa.CheckConstraint("thread_id LIKE entity || ':%'", name="runs_thread_under_entity"),
        schema="itp",
    )


def downgrade() -> None:
    op.drop_table("runs", schema="itp")
