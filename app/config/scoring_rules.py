"""Deterministic scoring, confidence, finance, and decision rules."""

from dataclasses import dataclass

SCORING_VERSION = "v1.0"

MIN_SCORE = 0
MAX_TOTAL_SCORE = 100


@dataclass(frozen=True)
class ComponentMaxScores:
    """Maximum scores for deterministic score components."""

    demand: int = 35
    competition: int = 25
    rent: int = 20
    premises: int = 10
    accessibility: int = 10


@dataclass(frozen=True)
class DemandRules:
    """Demand scoring weights."""

    base: int = 5
    high_density_area: int = 15
    new_residential_area: int = 15


@dataclass(frozen=True)
class CompetitionRules:
    """Competition scoring thresholds and weights."""

    radius_300m_zero: int = 10
    radius_300m_one: int = 7
    radius_300m_two: int = 4
    radius_300m_three_or_more: int = 1

    radius_700m_zero_to_two: int = 10
    radius_700m_three_to_four: int = 7
    radius_700m_five_to_six: int = 4
    radius_700m_seven_or_more: int = 1

    nearest_over_500m: int = 5
    nearest_300m_to_500m: int = 3
    nearest_150m_to_300m: int = 1
    nearest_under_150m: int = 0
    no_known_competitor: int = 5
    unknown_nearest_with_competitors: int = 0

    count_one: int = 1
    count_two: int = 2
    count_three: int = 3
    count_five: int = 5
    count_seven: int = 7
    distance_150m: int = 150
    distance_300m: int = 300
    distance_500m: int = 500


@dataclass(frozen=True)
class RentRules:
    """Rent score thresholds for Krasnodar MVP."""

    cheap_max: int = 60_000
    normal_max: int = 90_000
    high_max: int = 130_000
    cheap_score: int = 20
    normal_score: int = 15
    high_score: int = 8
    expensive_score: int = 2


@dataclass(frozen=True)
class PremisesRules:
    """Premises scoring weights and area thresholds."""

    first_floor: int = 3
    separate_entrance: int = 2
    ideal_area: int = 2
    acceptable_area: int = 1
    bad_area: int = 0
    storage_area: int = 2
    signage_possible: int = 1

    acceptable_area_min_exclusive: float = 15.0
    ideal_area_min: float = 20.0
    ideal_area_max: float = 60.0
    acceptable_area_max: float = 80.0


@dataclass(frozen=True)
class AccessibilityRules:
    """Accessibility scoring weights."""

    parking: int = 3
    bus_stop_nearby: int = 3
    good_visibility: int = 2
    separate_entrance: int = 2


@dataclass(frozen=True)
class ConfidenceRules:
    """Confidence score weights and thresholds."""

    source_completeness_two_or_more: int = 25
    source_completeness_one: int = 15
    source_completeness_none: int = 0

    freshness_under_7_days: int = 20
    freshness_under_30_days: int = 15
    freshness_old_or_unknown: int = 5
    freshness_days_7: int = 7
    freshness_days_30: int = 30

    manual_input_verified: int = 20
    manual_input_manual: int = 10
    manual_input_partial: int = 5

    competitor_count_three_or_more: int = 20
    competitor_count_one_to_two: int = 10
    competitor_count_none: int = 5

    finance_with_expected_income: int = 15
    finance_without_expected_income: int = 5

    source_count_one: int = 1
    source_count_two: int = 2
    competitor_count_one: int = 1
    competitor_count_three: int = 3


@dataclass(frozen=True)
class FinanceDefaults:
    """Default finance assumptions for Krasnodar PVZ MVP."""

    salary: int = 120_000
    taxes: int = 30_000
    utilities: int = 10_000
    internet: int = 5_000
    consumables: int = 10_000
    other_costs: int = 15_000
    reserve: int = 20_000
    desired_profit: int = 80_000
    investment: int = 600_000
    payback_round_digits: int = 1


@dataclass(frozen=True)
class DecisionRules:
    """Decision thresholds, labels, and warnings."""

    high_score_threshold: int = 75
    mid_score_threshold: int = 60
    high_rent_threshold: int = 130_000

    consider: str = "можно рассматривать"
    check_more: str = "проверить дополнительно"
    likely_no: str = "скорее не открывать"

    high_rent_warning: str = "Высокая аренда: проверьте устойчивость экономики ПВЗ."
    unprofitable_warning: str = "При указанном доходе точка убыточна."
    income_missing_warning: str = (
        "Доход не указан: финальная окупаемость не рассчитана."
    )


COMPONENT_MAX_SCORES = ComponentMaxScores()
DEMAND_RULES = DemandRules()
COMPETITION_RULES = CompetitionRules()
RENT_RULES = RentRules()
PREMISES_RULES = PremisesRules()
ACCESSIBILITY_RULES = AccessibilityRules()
CONFIDENCE_RULES = ConfidenceRules()
FINANCE_DEFAULTS = FinanceDefaults()
DECISION_RULES = DecisionRules()
