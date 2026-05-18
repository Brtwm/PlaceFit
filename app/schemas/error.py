"""Error response schemas."""

from typing import Literal

from app.schemas.common import AppBaseModel
from app.schemas.location import GeocodeCandidate

ErrorCode = Literal[
    "VALIDATION_ERROR",
    "GEOCODING_FAILED",
    "CITY_NOT_SUPPORTED",
    "ADDRESS_AMBIGUOUS",
    "COMPETITOR_SEARCH_FAILED",
    "LLM_FAILED",
    "NOT_FOUND",
    "INTERNAL_ERROR",
]


class ErrorInfo(AppBaseModel):
    """Structured API error payload."""

    code: ErrorCode
    message: str
    details: str | None = None
    suggestions: list[GeocodeCandidate] | None = None


class ErrorResponse(AppBaseModel):
    """Standard API error response."""

    error: ErrorInfo
