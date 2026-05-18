"""Report and marketplace requirement schemas."""

from datetime import datetime
from typing import Literal

from app.schemas.common import AppBaseModel, ConfidenceRatio


class MarketplaceRequirementResult(AppBaseModel):
    """Manual-check-only marketplace requirement result for MVP."""

    status: Literal["needs_manual_check"]
    needs_manual_check: Literal[True]
    manual_checks: list[str]
    warning: str


class MarketplaceRequirements(AppBaseModel):
    """Marketplace requirements fixed to MVP marketplaces."""

    ozon: MarketplaceRequirementResult
    wildberries: MarketplaceRequirementResult
    yandex_market: MarketplaceRequirementResult


class ReportResult(AppBaseModel):
    """AI or fallback report result."""

    status: Literal["success", "fallback"]
    text: str
    provider: Literal["openai_compatible", "fallback"]
    model: str
    prompt_version: str


class DataSourceInfo(AppBaseModel):
    """Source metadata included in analysis responses."""

    source: str
    data_type: str
    fetched_at: datetime
    confidence: ConfidenceRatio | None = None


class ReportGenerateRequest(AppBaseModel):
    """Request to regenerate a report for an existing analysis."""

    location_id: int
