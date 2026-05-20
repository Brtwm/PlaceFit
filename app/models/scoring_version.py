"""Scoring version ORM model."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ScoringVersion(Base):
    """Versioned deterministic scoring rules."""

    __tablename__ = "scoring_versions"
    __table_args__ = (
        UniqueConstraint(
            "business_type",
            "version",
            name="uq_scoring_versions_business_type_version",
        ),
        Index("idx_scoring_versions_business_type", "business_type"),
        Index(
            "ux_scoring_versions_one_active_per_business_type",
            "business_type",
            unique=True,
            postgresql_where=text("active"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_type: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(Text, nullable=False)
    rules: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )
