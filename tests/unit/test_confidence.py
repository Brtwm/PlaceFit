from datetime import date

from app.services.confidence import (
    ConfidenceInput,
    ManualInputReliability,
    calculate_confidence,
)

AS_OF_DATE = date(2026, 5, 19)


def confidence_input(**overrides: object) -> ConfidenceInput:
    data = {
        "poi_source_count": 2,
        "as_of_date": AS_OF_DATE,
        "freshness_date": date(2026, 5, 14),
        "manual_input_reliability": ManualInputReliability.MANUAL,
        "competitors_700m": 5,
        "expected_gross_income_by_user": 360_000,
    }
    data.update(overrides)
    return ConfidenceInput(**data)  # type: ignore[arg-type]


def test_docs_reference_example_confidence_is_90() -> None:
    result = calculate_confidence(confidence_input())

    assert result.confidence_score == 90


def test_source_completeness_two_or_more_sources() -> None:
    result = calculate_confidence(confidence_input(poi_source_count=2))

    assert result.details.source_completeness == 25


def test_source_completeness_one_source() -> None:
    result = calculate_confidence(confidence_input(poi_source_count=1))

    assert result.details.source_completeness == 15


def test_source_completeness_zero_sources() -> None:
    result = calculate_confidence(confidence_input(poi_source_count=0))

    assert result.details.source_completeness == 0


def test_fresh_under_7_days() -> None:
    result = calculate_confidence(confidence_input(freshness_date=date(2026, 5, 14)))

    assert result.details.freshness == 20


def test_fresh_under_30_days() -> None:
    result = calculate_confidence(confidence_input(freshness_date=date(2026, 5, 1)))

    assert result.details.freshness == 15


def test_old_over_30_days() -> None:
    result = calculate_confidence(confidence_input(freshness_date=date(2026, 4, 1)))

    assert result.details.freshness == 5


def test_unknown_freshness_is_low_confidence() -> None:
    result = calculate_confidence(confidence_input(freshness_date=None))

    assert result.details.freshness == 5


def test_expected_income_present_finance_confidence() -> None:
    result = calculate_confidence(
        confidence_input(expected_gross_income_by_user=360_000),
    )

    assert result.details.finance_data_confidence == 15


def test_expected_income_missing_finance_confidence() -> None:
    result = calculate_confidence(confidence_input(expected_gross_income_by_user=None))

    assert result.details.finance_data_confidence == 5


def test_zero_competitors_low_competitor_confidence() -> None:
    result = calculate_confidence(confidence_input(competitors_700m=0))

    assert result.details.competitor_data_confidence == 5


def test_one_to_two_competitors_medium_competitor_confidence() -> None:
    result = calculate_confidence(confidence_input(competitors_700m=2))

    assert result.details.competitor_data_confidence == 10


def test_three_or_more_competitors_high_competitor_confidence() -> None:
    result = calculate_confidence(confidence_input(competitors_700m=3))

    assert result.details.competitor_data_confidence == 20


def test_confidence_score_always_in_range() -> None:
    cases = [
        confidence_input(),
        confidence_input(
            poi_source_count=0,
            freshness_date=None,
            manual_input_reliability=ManualInputReliability.PARTIAL,
            competitors_700m=0,
            expected_gross_income_by_user=None,
        ),
        confidence_input(
            poi_source_count=10,
            freshness_date=date(2026, 5, 19),
            manual_input_reliability=ManualInputReliability.VERIFIED,
            competitors_700m=10,
        ),
    ]

    for case in cases:
        result = calculate_confidence(case)
        assert 0 <= result.confidence_score <= 100


def test_confidence_is_deterministic() -> None:
    input_data = confidence_input()

    assert calculate_confidence(input_data) == calculate_confidence(input_data)
