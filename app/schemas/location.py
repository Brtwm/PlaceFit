"""Location and geocoding API schemas."""

from datetime import date
from typing import Literal

from pydantic import Field

from app.schemas.common import (
    AppBaseModel,
    ConfidenceRatio,
    CreatedAt,
    Latitude,
    Longitude,
    PositiveFloat,
    PositiveInt,
    ScoreValue,
)


class LocationInfo(AppBaseModel):
    """Location data returned by analysis endpoints."""

    id: int
    address: str
    normalized_address: str
    lat: Latitude
    lon: Longitude


class LocationsListItem(AppBaseModel):
    """Compact location history item."""

    id: int
    address: str
    business_type: Literal["pvz"]
    rent: PositiveInt
    total_score: ScoreValue
    confidence_score: ScoreValue
    decision: str
    net_profit: int | None = None
    payback_months: PositiveFloat | None = None
    created_at: CreatedAt


class LocationsListResponse(AppBaseModel):
    """Response for the location history endpoint."""

    items: list[LocationsListItem]
    total: PositiveInt


class LocationsListRequest(AppBaseModel):
    """Query parameters for the location history endpoint."""

    business_type: Literal["pvz"] = "pvz"
    min_score: ScoreValue | None = None
    max_score: ScoreValue | None = None
    decision: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    limit: PositiveInt = Field(default=50, le=100)
    offset: PositiveInt = 0


class GeocodeRequest(AppBaseModel):
    """Request for address geocoding."""

    address: str


class GeocodeCandidate(AppBaseModel):
    """Single geocoding candidate."""

    address: str
    lat: Latitude
    lon: Longitude
    confidence: ConfidenceRatio | None = None


class GeocodeResponse(AppBaseModel):
    """Response for address geocoding."""

    results: list[GeocodeCandidate]
    source: str
