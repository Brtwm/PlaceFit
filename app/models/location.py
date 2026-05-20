"""Location ORM model."""

from datetime import datetime
from decimal import Decimal

from geoalchemy2 import Geography
from sqlalchemy import Boolean, DateTime, Index, Integer, Numeric, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Location(Base):
    """Analyzed address and user-provided premises fields."""

    __tablename__ = "locations"
    __table_args__ = (
        Index("idx_locations_geom", "geom", postgresql_using="gist"),
        Index("idx_locations_city", "city"),
        Index("idx_locations_business_type", "business_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(
        Text,
        server_default=text("'Краснодар'"),
    )
    region: Mapped[str | None] = mapped_column(Text)
    lat: Mapped[float | None]
    lon: Mapped[float | None]
    geom: Mapped[object | None] = mapped_column(
        Geography("POINT", srid=4326, spatial_index=False),
    )
    business_type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'pvz'"),
    )
    rent: Mapped[int | None] = mapped_column(Integer)
    area_m2: Mapped[Decimal | None] = mapped_column(Numeric)
    floor: Mapped[int | None] = mapped_column(Integer)
    first_floor: Mapped[bool | None] = mapped_column(Boolean)
    separate_entrance: Mapped[bool | None] = mapped_column(Boolean)
    parking: Mapped[bool | None] = mapped_column(Boolean)
    signage_possible: Mapped[bool | None] = mapped_column(Boolean)
    storage_area: Mapped[bool | None] = mapped_column(Boolean)
    repair_condition: Mapped[str | None] = mapped_column(Text)
    new_residential_area: Mapped[bool | None] = mapped_column(Boolean)
    high_density_area: Mapped[bool | None] = mapped_column(Boolean)
    bus_stop_nearby: Mapped[bool | None] = mapped_column(Boolean)
    good_visibility: Mapped[bool | None] = mapped_column(Boolean)
    source_url: Mapped[str | None] = mapped_column(Text)
    geocoding_source: Mapped[str | None] = mapped_column(Text)
    geocoding_fetched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    geocoding_confidence: Mapped[Decimal | None] = mapped_column(Numeric)
    user_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )
