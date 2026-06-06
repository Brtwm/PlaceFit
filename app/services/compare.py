"""Compare service for deterministic V1.2 candidate ranking."""

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.config.scoring_rules import DECISION_RULES
from app.models import CompareSession
from app.schemas.analysis import AnalysisResponse
from app.schemas.compare import (
    DEFAULT_COMPARE_RANKING_RULES,
    CompareCompetitorSummary,
    CompareFailedCandidate,
    CompareRequest,
    CompareResponse,
    CompareSuccessfulCandidate,
    CompareSummary,
)
from app.schemas.error import ErrorCode, ErrorInfo
from app.schemas.report import MarketplaceRequirements
from app.services.analysis import (
    AnalysisService,
    AnalysisServiceError,
    to_geocode_candidates,
)

_ASSUMPTIONS = [
    "expected_gross_income_by_user is a user hypothesis, not a system forecast.",
    "Marketplace requirements require manual verification from official sources.",
]
_DECISION_SEVERITY = {
    DECISION_RULES.consider: 0,
    DECISION_RULES.check_more: 1,
    DECISION_RULES.likely_no: 2,
}


@dataclass(frozen=True)
class _SuccessfulCandidateDraft:
    candidate_id: str
    input_index: int
    label: str | None
    input_address: str
    analysis: AnalysisResponse


class CompareServiceError(Exception):
    """Domain error raised by the compare service."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        details: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details


class CompareService:
    """Compare newly submitted candidates through the analysis pipeline."""

    def __init__(
        self,
        analysis_service: AnalysisService,
        *,
        db: Session | None = None,
    ) -> None:
        self._analysis_service = analysis_service
        self._db = db

    def compare(self, request: CompareRequest) -> CompareResponse:
        """Analyze, rank, and return visible per-candidate outcomes."""

        successful: list[_SuccessfulCandidateDraft] = []
        failed: list[CompareFailedCandidate] = []

        for input_index, candidate in enumerate(request.candidates):
            candidate_id = _candidate_id(input_index)
            try:
                analysis = self._analysis_service.analyze(
                    candidate.analysis_request,
                )
            except AnalysisServiceError as exc:
                failed.append(
                    _failed_candidate(
                        candidate_id=candidate_id,
                        input_index=input_index,
                        label=candidate.label,
                        input_address=candidate.analysis_request.address,
                        error=exc,
                    ),
                )
                continue

            successful.append(
                _SuccessfulCandidateDraft(
                    candidate_id=candidate_id,
                    input_index=input_index,
                    label=candidate.label,
                    input_address=candidate.analysis_request.address,
                    analysis=analysis,
                ),
            )

        ranked = [
            _successful_candidate(draft, rank=rank)
            for rank, draft in enumerate(
                sorted(successful, key=_ranking_key),
                start=1,
            )
        ]

        response = CompareResponse(
            compare_id=None,
            created_at=datetime.now(UTC),
            ranking_rules=DEFAULT_COMPARE_RANKING_RULES,
            ranked_candidates=ranked,
            failed_candidates=failed,
            summary=CompareSummary(
                requested_count=len(request.candidates),
                successful_count=len(ranked),
                failed_count=len(failed),
            ),
        )
        return self._save_compare_session(request, response)

    def get_saved_compare_session(self, compare_id: int) -> CompareResponse:
        """Return the original saved compare response snapshot."""

        if self._db is None:
            raise CompareServiceError("NOT_FOUND", "Сессия сравнения не найдена")

        session = self._db.get(CompareSession, compare_id)
        if session is None:
            raise CompareServiceError("NOT_FOUND", "Сессия сравнения не найдена")

        return CompareResponse.model_validate(session.response_snapshot)

    def _save_compare_session(
        self,
        request: CompareRequest,
        response: CompareResponse,
    ) -> CompareResponse:
        if self._db is None:
            return response

        session = CompareSession(
            ranking_rules_version=response.ranking_rules.version,
            request_snapshot=request.model_dump(mode="json"),
            response_snapshot=response.model_dump(mode="json"),
        )
        try:
            self._db.add(session)
            self._db.flush()
            response.compare_id = session.id
            session.response_snapshot = response.model_dump(mode="json")
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

        return response


def _candidate_id(input_index: int) -> str:
    return f"candidate-{input_index + 1}"


def _ranking_key(
    draft: _SuccessfulCandidateDraft,
) -> tuple[int, int, int, int, int, int, float, int]:
    analysis = draft.analysis
    return (
        -analysis.score.total_score,
        -analysis.score.confidence_score,
        _decision_severity(analysis.score.decision),
        *_net_profit_key(analysis.finance.net_profit),
        *_payback_key(analysis.finance.payback_months),
        draft.input_index,
    )


def _decision_severity(decision: str) -> int:
    return _DECISION_SEVERITY.get(decision, len(_DECISION_SEVERITY))


def _net_profit_key(value: int | None) -> tuple[int, int]:
    if value is None:
        return (1, 0)
    return (0, -value)


def _payback_key(value: float | None) -> tuple[int, float]:
    if value is None:
        return (1, 0.0)
    return (0, value)


def _successful_candidate(
    draft: _SuccessfulCandidateDraft,
    *,
    rank: int,
) -> CompareSuccessfulCandidate:
    analysis = draft.analysis
    return CompareSuccessfulCandidate(
        candidate_id=draft.candidate_id,
        input_index=draft.input_index,
        rank=rank,
        label=draft.label,
        input_address=draft.input_address,
        status="success",
        source_analysis_id=analysis.location.id,
        location_summary=analysis.location,
        score=analysis.score,
        finance=analysis.finance,
        competitors=CompareCompetitorSummary(
            competitors_300m=analysis.competitors.competitors_300m,
            competitors_500m=analysis.competitors.competitors_500m,
            competitors_700m=analysis.competitors.competitors_700m,
            nearest_competitor_distance_m=(
                analysis.competitors.nearest_competitor_distance_m
            ),
            average_competitor_distance_m=(
                analysis.competitors.average_competitor_distance_m
            ),
        ),
        assumptions=list(_ASSUMPTIONS),
        warnings=_marketplace_warnings(analysis.marketplace_requirements),
        trade_offs=[],
    )


def _marketplace_warnings(
    marketplace_requirements: MarketplaceRequirements,
) -> list[str]:
    warnings: list[str] = []
    for requirement in (
        marketplace_requirements.ozon,
        marketplace_requirements.wildberries,
        marketplace_requirements.yandex_market,
    ):
        if requirement.warning not in warnings:
            warnings.append(requirement.warning)
    return warnings


def _failed_candidate(
    *,
    candidate_id: str,
    input_index: int,
    label: str | None,
    input_address: str,
    error: AnalysisServiceError,
) -> CompareFailedCandidate:
    return CompareFailedCandidate(
        candidate_id=candidate_id,
        input_index=input_index,
        label=label,
        input_address=input_address,
        status="failed",
        error=ErrorInfo(
            code=error.code,
            message=error.message,
            details=error.details,
            suggestions=to_geocode_candidates(error.suggestions)
            if error.suggestions
            else None,
        ),
    )
