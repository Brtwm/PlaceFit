"""Pure deterministic rule-based scoring service."""

from dataclasses import dataclass

from app.config.scoring_rules import (
    ACCESSIBILITY_RULES,
    COMPETITION_RULES,
    COMPONENT_MAX_SCORES,
    DEMAND_RULES,
    MAX_TOTAL_SCORE,
    MIN_SCORE,
    PREMISES_RULES,
    RENT_RULES,
    SCORING_VERSION,
)


@dataclass(frozen=True)
class ScoringInput:
    """Input fields required by deterministic scoring v1.0."""

    high_density_area: bool
    new_residential_area: bool
    competitors_300m: int
    competitors_700m: int
    nearest_competitor_distance_m: int | None
    rent: int
    first_floor: bool
    separate_entrance: bool
    area_m2: float
    storage_area: bool
    signage_possible: bool
    parking: bool
    bus_stop_nearby: bool
    good_visibility: bool


@dataclass(frozen=True)
class ScoreDetails:
    """Component score breakdown."""

    demand_score: int
    competition_score: int
    rent_score: int
    premises_score: int
    accessibility_score: int


@dataclass(frozen=True)
class ScoringResult:
    """Full deterministic score result."""

    total_score: int
    details: ScoreDetails
    scoring_version: str


def calculate_score(input_data: ScoringInput) -> ScoringResult:
    """Calculate deterministic scoring v1.0 for a PVZ location."""

    details = ScoreDetails(
        demand_score=_demand_score(input_data),
        competition_score=_competition_score(input_data),
        rent_score=_rent_score(input_data.rent),
        premises_score=_premises_score(input_data),
        accessibility_score=_accessibility_score(input_data),
    )
    total_score = _clamp(
        details.demand_score
        + details.competition_score
        + details.rent_score
        + details.premises_score
        + details.accessibility_score,
        MAX_TOTAL_SCORE,
    )

    return ScoringResult(
        total_score=total_score,
        details=details,
        scoring_version=SCORING_VERSION,
    )


def _demand_score(input_data: ScoringInput) -> int:
    score = DEMAND_RULES.base
    if input_data.high_density_area:
        score += DEMAND_RULES.high_density_area
    if input_data.new_residential_area:
        score += DEMAND_RULES.new_residential_area
    return _clamp(score, COMPONENT_MAX_SCORES.demand)


def _competition_score(input_data: ScoringInput) -> int:
    score = (
        _competitors_300m_score(input_data.competitors_300m)
        + _competitors_700m_score(input_data.competitors_700m)
        + _nearest_competitor_score(
            competitors_700m=input_data.competitors_700m,
            nearest_competitor_distance_m=input_data.nearest_competitor_distance_m,
        )
    )
    return _clamp(score, COMPONENT_MAX_SCORES.competition)


def _competitors_300m_score(competitors_300m: int) -> int:
    if competitors_300m <= MIN_SCORE:
        return COMPETITION_RULES.radius_300m_zero
    if competitors_300m == COMPETITION_RULES.count_one:
        return COMPETITION_RULES.radius_300m_one
    if competitors_300m == COMPETITION_RULES.count_two:
        return COMPETITION_RULES.radius_300m_two
    return COMPETITION_RULES.radius_300m_three_or_more


def _competitors_700m_score(competitors_700m: int) -> int:
    if competitors_700m <= COMPETITION_RULES.count_two:
        return COMPETITION_RULES.radius_700m_zero_to_two
    if competitors_700m < COMPETITION_RULES.count_five:
        return COMPETITION_RULES.radius_700m_three_to_four
    if competitors_700m < COMPETITION_RULES.count_seven:
        return COMPETITION_RULES.radius_700m_five_to_six
    return COMPETITION_RULES.radius_700m_seven_or_more


def _nearest_competitor_score(
    *,
    competitors_700m: int,
    nearest_competitor_distance_m: int | None,
) -> int:
    if nearest_competitor_distance_m is None:
        if competitors_700m <= MIN_SCORE:
            return COMPETITION_RULES.no_known_competitor
        return COMPETITION_RULES.unknown_nearest_with_competitors
    if nearest_competitor_distance_m > COMPETITION_RULES.distance_500m:
        return COMPETITION_RULES.nearest_over_500m
    if nearest_competitor_distance_m >= COMPETITION_RULES.distance_300m:
        return COMPETITION_RULES.nearest_300m_to_500m
    if nearest_competitor_distance_m >= COMPETITION_RULES.distance_150m:
        return COMPETITION_RULES.nearest_150m_to_300m
    return COMPETITION_RULES.nearest_under_150m


def _rent_score(rent: int) -> int:
    if rent <= RENT_RULES.cheap_max:
        return RENT_RULES.cheap_score
    if rent <= RENT_RULES.normal_max:
        return RENT_RULES.normal_score
    if rent <= RENT_RULES.high_max:
        return RENT_RULES.high_score
    return RENT_RULES.expensive_score


def _premises_score(input_data: ScoringInput) -> int:
    score = MIN_SCORE
    if input_data.first_floor:
        score += PREMISES_RULES.first_floor
    if input_data.separate_entrance:
        score += PREMISES_RULES.separate_entrance
    score += _area_score(input_data.area_m2)
    if input_data.storage_area:
        score += PREMISES_RULES.storage_area
    if input_data.signage_possible:
        score += PREMISES_RULES.signage_possible
    return _clamp(score, COMPONENT_MAX_SCORES.premises)


def _area_score(area_m2: float) -> int:
    if (
        PREMISES_RULES.ideal_area_min
        <= area_m2
        <= PREMISES_RULES.ideal_area_max
    ):
        return PREMISES_RULES.ideal_area
    if (
        PREMISES_RULES.acceptable_area_min_exclusive
        < area_m2
        < PREMISES_RULES.ideal_area_min
    ) or (
        PREMISES_RULES.ideal_area_max
        < area_m2
        <= PREMISES_RULES.acceptable_area_max
    ):
        return PREMISES_RULES.acceptable_area
    return PREMISES_RULES.bad_area


def _accessibility_score(input_data: ScoringInput) -> int:
    score = MIN_SCORE
    if input_data.parking:
        score += ACCESSIBILITY_RULES.parking
    if input_data.bus_stop_nearby:
        score += ACCESSIBILITY_RULES.bus_stop_nearby
    if input_data.good_visibility:
        score += ACCESSIBILITY_RULES.good_visibility
    if input_data.separate_entrance:
        score += ACCESSIBILITY_RULES.separate_entrance
    return _clamp(score, COMPONENT_MAX_SCORES.accessibility)


def _clamp(score: int, max_score: int) -> int:
    return max(MIN_SCORE, min(score, max_score))
