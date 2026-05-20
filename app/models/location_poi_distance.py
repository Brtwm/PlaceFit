"""Location-to-POI distance ORM model."""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LocationPoiDistance(Base):
    """Cached distance between a location and a POI."""

    __tablename__ = "location_poi_distances"
    __table_args__ = (
        UniqueConstraint(
            "location_id",
            "poi_id",
            name="uq_location_poi_distances_location_poi",
        ),
        Index("idx_location_poi_distances_location_id", "location_id"),
        Index("idx_location_poi_distances_poi_id", "poi_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
    )
    poi_id: Mapped[int] = mapped_column(
        ForeignKey("pois.id", ondelete="CASCADE"),
        nullable=False,
    )
    distance_m: Mapped[int] = mapped_column(Integer, nullable=False)
    radius_bucket: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )
