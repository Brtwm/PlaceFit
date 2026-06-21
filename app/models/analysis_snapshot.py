"""Immutable analysis snapshot ORM model."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AnalysisSnapshot(Base):
    """Validated public request and response for one persisted analysis."""

    __tablename__ = "analysis_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "previous_location_id",
            name="uq_analysis_snapshots_previous_location_id",
        ),
        CheckConstraint(
            "origin IN ('native', 'legacy_materialized')",
            name="ck_analysis_snapshots_origin",
        ),
        CheckConstraint(
            "length(snapshot_schema_version) > 0",
            name="ck_analysis_snapshots_schema_version_not_empty",
        ),
        CheckConstraint(
            "(root_location_id = location_id AND previous_location_id IS NULL) "
            "OR (root_location_id <> location_id "
            "AND previous_location_id IS NOT NULL)",
            name="ck_analysis_snapshots_lineage_shape",
        ),
        Index(
            "idx_analysis_snapshots_root_created_location",
            "root_location_id",
            "created_at",
            "location_id",
        ),
    )

    location_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("locations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    root_location_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
    )
    previous_location_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("locations.id", ondelete="RESTRICT"),
    )
    request_snapshot: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
    )
    response_snapshot: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
    )
    snapshot_schema_version: Mapped[str] = mapped_column(Text, nullable=False)
    origin: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )
