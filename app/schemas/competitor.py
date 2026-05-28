"""Competitor API schemas."""

from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.common import (
    AppBaseModel,
    Latitude,
    Longitude,
    PositiveFloat,
    PositiveInt,
)


class CompetitorInfo(AppBaseModel):
    """Single competitor point near an analyzed location."""

    name: str
    brand: str
    category: str
    address: str
    lat: Latitude | None = None
    lon: Longitude | None = None
    distance_m: PositiveInt
    rating: PositiveFloat | None = None
    reviews_count: PositiveInt | None = None
    source: str


class CompetitorsSummary(AppBaseModel):
    """Competitor counts and nearest-distance summary."""

    competitors_300m: PositiveInt
    competitors_500m: PositiveInt
    competitors_700m: PositiveInt
    nearest_competitor_distance_m: PositiveInt | None = None
    average_competitor_distance_m: PositiveInt | None = None
    list: list[CompetitorInfo]


class CompetitorsSearchRequest(AppBaseModel):
    """Request for competitor search near a coordinate."""

    lat: Latitude
    lon: Longitude
    radius_m: PositiveInt = Field(default=700, gt=0)
    business_type: Literal["pvz"]


class CompetitorCounts(AppBaseModel):
    """Competitor counts by MVP radii."""

    radius_300m: PositiveInt = Field(alias="300m")
    radius_500m: PositiveInt = Field(alias="500m")
    radius_700m: PositiveInt = Field(alias="700m")


class CompetitorsSearchResponse(AppBaseModel):
    """Response for competitor search."""

    competitors: list[CompetitorInfo]
    counts: CompetitorCounts
    source: str
    fetched_at: datetime
