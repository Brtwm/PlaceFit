"""Compare session ORM model."""

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CompareSession(Base):
    """Snapshot of a deterministic compare run."""

    __tablename__ = "compare_sessions"
    __table_args__ = (Index("idx_compare_sessions_created_at", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )
    ranking_rules_version: Mapped[str] = mapped_column(Text, nullable=False)
    request_snapshot: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
    )
    response_snapshot: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text)
