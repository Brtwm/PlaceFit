"""Create immutable analysis snapshots table.

Revision ID: 0003_create_analysis_snapshots
Revises: 0002_create_compare_sessions
Create Date: 2026-06-21
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_create_analysis_snapshots"
down_revision = "0002_create_compare_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create immutable request and response snapshot storage."""

    op.create_table(
        "analysis_snapshots",
        sa.Column(
            "location_id",
            sa.Integer(),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "root_location_id",
            sa.Integer(),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "previous_location_id",
            sa.Integer(),
            sa.ForeignKey("locations.id", ondelete="RESTRICT"),
            nullable=True,
        ),
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
        sa.Column("snapshot_schema_version", sa.Text(), nullable=False),
        sa.Column("origin", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "previous_location_id",
            name="uq_analysis_snapshots_previous_location_id",
        ),
        sa.CheckConstraint(
            "origin IN ('native', 'legacy_materialized')",
            name="ck_analysis_snapshots_origin",
        ),
        sa.CheckConstraint(
            "length(snapshot_schema_version) > 0",
            name="ck_analysis_snapshots_schema_version_not_empty",
        ),
        sa.CheckConstraint(
            "(root_location_id = location_id AND previous_location_id IS NULL) "
            "OR (root_location_id <> location_id "
            "AND previous_location_id IS NOT NULL)",
            name="ck_analysis_snapshots_lineage_shape",
        ),
    )
    op.create_index(
        "idx_analysis_snapshots_root_created_location",
        "analysis_snapshots",
        ["root_location_id", "created_at", "location_id"],
    )


def downgrade() -> None:
    """Drop only immutable analysis snapshot storage."""

    op.drop_index(
        "idx_analysis_snapshots_root_created_location",
        table_name="analysis_snapshots",
    )
    op.drop_table("analysis_snapshots")
