"""Fallback-first report generation service."""

from typing import Literal

from pydantic import ValidationError

from app.config.settings import Settings
from app.providers.llm.base import LlmReportProvider
from app.schemas.common import AppBaseModel, Latitude, Longitude
from app.schemas.competitor import CompetitorsSummary
from app.schemas.finance import FinanceResult
from app.schemas.report import (
    DataSourceInfo,
    MarketplaceRequirements,
    ReportResult,
)
from app.schemas.score import ScoreResult


class ReportServiceError(Exception):
    """Raised when neither LLM nor fallback can create a valid report."""


class PreparedReportLocation(AppBaseModel):
    """Safe location fields allowed in the LLM report payload."""

    address: str
    normalized_address: str
    city: str
    business_type: Literal["pvz"]
    lat: Latitude
    lon: Longitude


class PreparedAnalysisReportInput(AppBaseModel):
    """Safe, deterministic analysis payload for report generation."""

    location: PreparedReportLocation
    competitors: CompetitorsSummary
    score: ScoreResult
    finance: FinanceResult
    marketplace_requirements: MarketplaceRequirements
    checklist: list[str]
    data_sources: list[DataSourceInfo]


class ReportService:
    """Select LLM or fallback provider and validate the public report result."""

    def __init__(
        self,
        *,
        settings: Settings,
        llm_provider: LlmReportProvider | None,
        fallback_provider: LlmReportProvider,
    ) -> None:
        self._settings = settings
        self._llm_provider = llm_provider
        self._fallback_provider = fallback_provider

    def generate_report(
        self,
        report_input: PreparedAnalysisReportInput,
    ) -> ReportResult:
        """Generate a report, falling back when LLM is disabled or fails."""

        if self._should_try_llm():
            try:
                return _validate_report_result(
                    self._llm_provider.generate(report_input)
                    if self._llm_provider is not None
                    else None,
                )
            except Exception:
                return self._generate_fallback(report_input)

        return self._generate_fallback(report_input)

    def _should_try_llm(self) -> bool:
        return (
            self._settings.llm_enabled
            and bool(self._settings.llm_api_key.strip())
            and self._llm_provider is not None
        )

    def _generate_fallback(
        self,
        report_input: PreparedAnalysisReportInput,
    ) -> ReportResult:
        try:
            return _validate_report_result(
                self._fallback_provider.generate(report_input),
            )
        except Exception as exc:
            raise ReportServiceError("Fallback report generation failed") from exc


def _validate_report_result(value: object) -> ReportResult:
    try:
        return ReportResult.model_validate(value)
    except ValidationError as exc:
        raise ReportServiceError("Report provider returned invalid result") from exc
