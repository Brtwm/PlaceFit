"""Point-of-interest ORM model."""

from datetime import datetime
from decimal import Decimal

from geoalchemy2 import Geography
from sqlalchemy import DateTime, Index, Integer, Numeric, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Poi(Base):
    """Competitor or relevant point of interest."""

    __tablename__ = "pois"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_pois_source_external_id"),
        Index("idx_pois_geom", "geom", postgresql_using="gist"),
        Index("idx_pois_brand", "brand"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str | None] = mapped_column(Text)
    brand: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    lat: Mapped[float | None]
    lon: Mapped[float | None]
    geom: Mapped[object | None] = mapped_column(
        Geography("POINT", srid=4326, spatial_index=False),
    )
    rating: Mapped[Decimal | None] = mapped_column(Numeric)
    reviews_count: Mapped[int | None] = mapped_column(Integer)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )
