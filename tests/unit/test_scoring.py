from app.services.scoring import ScoringInput, calculate_score


def scoring_input(**overrides: object) -> ScoringInput:
    data = {
        "high_density_area": True,
        "new_residential_area": True,
        "competitors_300m": 1,
        "competitors_700m": 5,
        "nearest_competitor_distance_m": 180,
        "rent": 85_000,
        "first_floor": True,
        "separate_entrance": True,
        "area_m2": 35.0,
        "storage_area": True,
        "signage_possible": True,
        "parking": True,
        "bus_stop_nearby": True,
        "good_visibility": True,
    }
    data.update(overrides)
    return ScoringInput(**data)  # type: ignore[arg-type]


def test_demand_score_all_true() -> None:
    result = calculate_score(
        scoring_input(high_density_area=True, new_residential_area=True),
    )

    assert result.details.demand_score == 35


def test_demand_score_all_false() -> None:
    result = calculate_score(
        scoring_input(high_density_area=False, new_residential_area=False),
    )

    assert result.details.demand_score == 5


def test_demand_score_one_signal_true() -> None:
    result = calculate_score(
        scoring_input(high_density_area=True, new_residential_area=False),
    )

    assert result.details.demand_score == 20


def test_competition_score_no_competitors() -> None:
    result = calculate_score(
        scoring_input(
            competitors_300m=0,
            competitors_700m=0,
            nearest_competitor_distance_m=None,
        ),
    )

    assert result.details.competition_score == 25


def test_competition_score_many_close_competitors_is_low_non_negative() -> None:
    result = calculate_score(
        scoring_input(
            competitors_300m=5,
            competitors_700m=10,
            nearest_competitor_distance_m=100,
        ),
    )

    assert 0 <= result.details.competition_score <= 5


def test_rent_score_cheap() -> None:
    result = calculate_score(scoring_input(rent=60_000))

    assert result.details.rent_score == 20


def test_rent_score_expensive() -> None:
    result = calculate_score(scoring_input(rent=130_001))

    assert result.details.rent_score == 2


def test_premises_score_ideal() -> None:
    result = calculate_score(
        scoring_input(
            first_floor=True,
            separate_entrance=True,
            area_m2=35.0,
            storage_area=True,
            signage_possible=True,
        ),
    )

    assert result.details.premises_score == 10


def test_accessibility_score_full() -> None:
    result = calculate_score(
        scoring_input(
            parking=True,
            bus_stop_nearby=True,
            good_visibility=True,
            separate_entrance=True,
        ),
    )

    assert result.details.accessibility_score == 10


def test_total_score_always_in_range() -> None:
    cases = [
        scoring_input(),
        scoring_input(
            high_density_area=False,
            new_residential_area=False,
            competitors_300m=20,
            competitors_700m=30,
            nearest_competitor_distance_m=50,
            rent=250_000,
            first_floor=False,
            separate_entrance=False,
            area_m2=100.0,
            storage_area=False,
            signage_possible=False,
            parking=False,
            bus_stop_nearby=False,
            good_visibility=False,
        ),
        scoring_input(
            competitors_300m=-1,
            competitors_700m=-1,
            nearest_competitor_distance_m=None,
        ),
    ]

    for case in cases:
        result = calculate_score(case)
        assert 0 <= result.total_score <= 100


def test_total_score_is_deterministic() -> None:
    input_data = scoring_input()

    assert calculate_score(input_data) == calculate_score(input_data)


def test_api_contract_like_case_total_score_is_82() -> None:
    result = calculate_score(scoring_input())

    assert result.total_score == 82
    assert result.details.demand_score == 35
    assert result.details.competition_score == 12
    assert result.details.rent_score == 15
    assert result.details.premises_score == 10
    assert result.details.accessibility_score == 10
    assert result.scoring_version == "v1.0"
