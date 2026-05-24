"""LLM report provider protocol."""

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.schemas.report import ReportResult

if TYPE_CHECKING:
    from app.services.report import PreparedAnalysisReportInput


class LlmProviderError(Exception):
    """Raised when an LLM provider cannot produce a valid report."""


@runtime_checkable
class LlmReportProvider(Protocol):
    """Provider capable of generating a public report result."""

    def generate(self, report_input: "PreparedAnalysisReportInput") -> ReportResult:
        """Generate a report from safe prepared analysis data."""
