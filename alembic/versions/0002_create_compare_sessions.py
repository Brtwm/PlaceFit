"""Create compare sessions table.

Revision ID: 0002_create_compare_sessions
Revises: 0001_create_mvp_schema
Create Date: 2026-06-01
"""

from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_create_compare_sessions"
down_revision = "0001_create_mvp_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create snapshot-first compare session storage."""

    op.create_table(
        "compare_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("ranking_rules_version", sa.Text(), nullable=False),
        sa.Column(
            "request_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "response_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index(
        "idx_compare_sessions_created_at",
        "compare_sessions",
        ["created_at"],
    )


def downgrade() -> None:
    """Drop compare session storage."""

    op.drop_index("idx_compare_sessions_created_at", table_name="compare_sessions")
    op.drop_table("compare_sessions")
