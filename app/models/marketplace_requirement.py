"""Marketplace requirement ORM model."""

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MarketplaceRequirement(Base):
    """Manual-check-only marketplace requirement reference row."""

    __tablename__ = "marketplace_requirements"
    __table_args__ = (
        UniqueConstraint(
            "marketplace",
            "business_type",
            "requirement_key",
            name="uq_marketplace_requirements_marketplace_business_key",
        ),
        Index("idx_marketplace_requirements_marketplace", "marketplace"),
        Index("idx_marketplace_requirements_business_type", "business_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    marketplace: Mapped[str] = mapped_column(Text, nullable=False)
    business_type: Mapped[str] = mapped_column(Text, nullable=False)
    requirement_key: Mapped[str] = mapped_column(Text, nullable=False)
    requirement_value: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    active: Mapped[bool | None] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )
