"""Pure deterministic confidence scoring service."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from app.config.scoring_rules import (
    CONFIDENCE_RULES,
    MAX_TOTAL_SCORE,
    MIN_SCORE,
)


class ManualInputReliability(StrEnum):
    """Reliability levels for manually supplied key fields."""

    VERIFIED = "verified"
    MANUAL = "manual"
    PARTIAL = "partial"


@dataclass(frozen=True)
class ConfidenceInput:
    """Input fields required by deterministic confidence scoring."""

    poi_source_count: int
    as_of_date: date
    freshness_date: date | None
    manual_input_reliability: ManualInputReliability
    competitors_700m: int
    expected_gross_income_by_user: int | None


@dataclass(frozen=True)
class ConfidenceDetails:
    """Confidence component breakdown."""

    source_completeness: int
    freshness: int
    manual_input_reliability: int
    competitor_data_confidence: int
    finance_data_confidence: int


@dataclass(frozen=True)
class ConfidenceResult:
    """Full deterministic confidence result."""

    confidence_score: int
    details: ConfidenceDetails


def calculate_confidence(input_data: ConfidenceInput) -> ConfidenceResult:
    """Calculate deterministic confidence score without reading current time."""

    details = ConfidenceDetails(
        source_completeness=_source_completeness(input_data.poi_source_count),
        freshness=_freshness(
            as_of_date=input_data.as_of_date,
            freshness_date=input_data.freshness_date,
        ),
        manual_input_reliability=_manual_input_reliability(
            input_data.manual_input_reliability,
        ),
        competitor_data_confidence=_competitor_data_confidence(
            input_data.competitors_700m,
        ),
        finance_data_confidence=_finance_data_confidence(
            input_data.expected_gross_income_by_user,
        ),
    )
    confidence_score = _clamp(
        details.source_completeness
        + details.freshness
        + details.manual_input_reliability
        + details.competitor_data_confidence
        + details.finance_data_confidence,
        MAX_TOTAL_SCORE,
    )

    return ConfidenceResult(confidence_score=confidence_score, details=details)


def _source_completeness(poi_source_count: int) -> int:
    if poi_source_count >= CONFIDENCE_RULES.source_count_two:
        return CONFIDENCE_RULES.source_completeness_two_or_more
    if poi_source_count == CONFIDENCE_RULES.source_count_one:
        return CONFIDENCE_RULES.source_completeness_one
    return CONFIDENCE_RULES.source_completeness_none


def _freshness(*, as_of_date: date, freshness_date: date | None) -> int:
    if freshness_date is None:
        return CONFIDENCE_RULES.freshness_old_or_unknown

    age_days = max((as_of_date - freshness_date).days, MIN_SCORE)
    if age_days < CONFIDENCE_RULES.freshness_days_7:
        return CONFIDENCE_RULES.freshness_under_7_days
    if age_days < CONFIDENCE_RULES.freshness_days_30:
        return CONFIDENCE_RULES.freshness_under_30_days
    return CONFIDENCE_RULES.freshness_old_or_unknown


def _manual_input_reliability(reliability: ManualInputReliability) -> int:
    if reliability is ManualInputReliability.VERIFIED:
        return CONFIDENCE_RULES.manual_input_verified
    if reliability is ManualInputReliability.MANUAL:
        return CONFIDENCE_RULES.manual_input_manual
    return CONFIDENCE_RULES.manual_input_partial


def _competitor_data_confidence(competitors_700m: int) -> int:
    if competitors_700m >= CONFIDENCE_RULES.competitor_count_three:
        return CONFIDENCE_RULES.competitor_count_three_or_more
    if competitors_700m >= CONFIDENCE_RULES.competitor_count_one:
        return CONFIDENCE_RULES.competitor_count_one_to_two
    return CONFIDENCE_RULES.competitor_count_none


def _finance_data_confidence(expected_gross_income_by_user: int | None) -> int:
    if expected_gross_income_by_user is None:
        return CONFIDENCE_RULES.finance_without_expected_income
    return CONFIDENCE_RULES.finance_with_expected_income


def _clamp(score: int, max_score: int) -> int:
    return max(MIN_SCORE, min(score, max_score))
