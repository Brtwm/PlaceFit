"""Compare API schemas for V1.2 contract work."""

from typing import Literal

from pydantic import Field

from app.config.scoring_rules import DECISION_RULES
from app.schemas.analysis import AnalysisRequest
from app.schemas.common import AppBaseModel, CreatedAt, PositiveInt
from app.schemas.error import ErrorInfo
from app.schemas.finance import FinanceResult
from app.schemas.location import LocationInfo
from app.schemas.score import ScoreResult

COMPARE_RANKING_VERSION = "v1.2-2"
COMPARE_DECISION_SEVERITY_ORDER = [
    DECISION_RULES.consider,
    DECISION_RULES.check_more,
    DECISION_RULES.likely_no,
]


class CompareCandidateRequest(AppBaseModel):
    """Single candidate submitted for a future compare run."""

    label: str | None = Field(default=None, min_length=1)
    analysis_request: AnalysisRequest


class CompareRequest(AppBaseModel):
    """Request contract for comparing 2-5 newly submitted candidates."""

    candidates: list[CompareCandidateRequest] = Field(min_length=2, max_length=5)


class CompareCompetitorSummary(AppBaseModel):
    """Competitor counts and distance summary used in compare rows."""

    competitors_300m: PositiveInt
    competitors_500m: PositiveInt
    competitors_700m: PositiveInt
    nearest_competitor_distance_m: PositiveInt | None = None
    average_competitor_distance_m: PositiveInt | None = None


class CompareSuccessfulCandidate(AppBaseModel):
    """Successful candidate result included in deterministic ranking."""

    candidate_id: str
    input_index: PositiveInt
    rank: int = Field(ge=1)
    label: str | None = None
    input_address: str
    status: Literal["success"]
    source_analysis_id: int | None = Field(default=None, ge=1)
    location_summary: LocationInfo
    score: ScoreResult
    finance: FinanceResult
    competitors: CompareCompetitorSummary
    assumptions: list[str]
    warnings: list[str]
    trade_offs: list[str]


class CompareFailedCandidate(AppBaseModel):
    """Candidate-level failure that does not necessarily fail the whole compare."""

    candidate_id: str
    input_index: PositiveInt
    label: str | None = None
    input_address: str
    status: Literal["failed"]
    error: ErrorInfo


class CompareRankingSortKey(AppBaseModel):
    """Single deterministic ranking key exposed for transparency."""

    field: str
    direction: Literal["asc", "desc"]
    nulls: Literal["first", "last", "none"]
    description: str


class CompareRankingRules(AppBaseModel):
    """Deterministic ranking metadata for compare responses."""

    version: str
    description: str
    sort_keys: list[CompareRankingSortKey]
    decision_severity_order: list[str]
    uses_llm: Literal[False] = False


class CompareSummary(AppBaseModel):
    """Top-level compare response counts."""

    requested_count: PositiveInt
    successful_count: PositiveInt
    failed_count: PositiveInt


class CompareResponse(AppBaseModel):
    """Response contract for a future compare endpoint."""

    compare_id: int | None = Field(default=None, ge=1)
    created_at: CreatedAt
    ranking_rules: CompareRankingRules
    ranked_candidates: list[CompareSuccessfulCandidate]
    failed_candidates: list[CompareFailedCandidate]
    summary: CompareSummary


DEFAULT_COMPARE_RANKING_RULES = CompareRankingRules(
    version=COMPARE_RANKING_VERSION,
    description=(
        "Successful candidates are ranked deterministically from visible "
        "analysis fields. LLM output is not used for ranking."
    ),
    sort_keys=[
        CompareRankingSortKey(
            field="score.total_score",
            direction="desc",
            nulls="none",
            description="Higher deterministic total score ranks first.",
        ),
        CompareRankingSortKey(
            field="score.confidence_score",
            direction="desc",
            nulls="none",
            description="Higher deterministic confidence breaks score ties.",
        ),
        CompareRankingSortKey(
            field="score.decision",
            direction="asc",
            nulls="none",
            description="Decision severity order breaks remaining ties.",
        ),
        CompareRankingSortKey(
            field="finance.net_profit",
            direction="desc",
            nulls="last",
            description="Higher known net profit breaks remaining ties.",
        ),
        CompareRankingSortKey(
            field="finance.payback_months",
            direction="asc",
            nulls="last",
            description="Shorter payback breaks ties when available.",
        ),
        CompareRankingSortKey(
            field="input_index",
            direction="asc",
            nulls="none",
            description="Original input order is the final stable tie-break.",
        ),
    ],
    decision_severity_order=COMPARE_DECISION_SEVERITY_ORDER,
    uses_llm=False,
)
