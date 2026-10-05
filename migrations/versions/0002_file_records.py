"""file_records: every stored file with provenance (T-106).

Revision ID: 0002_file_records
Revises: 0001_run_ledger
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_file_records"
down_revision: str | None = "0001_run_ledger"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "file_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("entity", sa.String(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("sender", sa.String()),
        sa.Column("object_key", sa.String(), nullable=False),
        sa.Column("mime_type", sa.String(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("untrusted_text_id", sa.Uuid()),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.UniqueConstraint("entity", "sha256", name="file_records_entity_sha256_key"),
        sa.CheckConstraint("sha256 ~ '^[a-f0-9]{64}$'", name="file_records_sha256_hex"),
        sa.CheckConstraint(
            "object_key LIKE entity || '/%'", name="file_records_object_key_under_entity"
        ),
        sa.CheckConstraint(
            "size_bytes > 0 AND size_bytes <= 20000000", name="file_records_size_bounds"
        ),
        schema="itp",
    )


def downgrade() -> None:
    op.drop_table("file_records", schema="itp")
