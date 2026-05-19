from app.config.scoring_rules import DECISION_RULES
from app.services.decision import make_decision


def test_high_score_positive_profit_consider() -> None:
    result = make_decision(total_score=82, rent=85_000, net_profit=65_000)

    assert result.decision == "можно рассматривать"


def test_high_score_without_income_consider() -> None:
    result = make_decision(total_score=82, rent=85_000, net_profit=None)

    assert result.decision == "можно рассматривать"


def test_high_score_negative_profit_check_more() -> None:
    result = make_decision(total_score=82, rent=85_000, net_profit=-10_000)

    assert result.decision == "проверить дополнительно"


def test_mid_score_check_more() -> None:
    result = make_decision(total_score=65, rent=85_000, net_profit=50_000)

    assert result.decision == "проверить дополнительно"


def test_low_scores_likely_no() -> None:
    assert (
        make_decision(total_score=50, rent=85_000, net_profit=50_000).decision
        == "скорее не открывать"
    )
    assert (
        make_decision(total_score=59, rent=85_000, net_profit=50_000).decision
        == "скорее не открывать"
    )


def test_high_rent_adds_warning() -> None:
    result = make_decision(total_score=82, rent=130_001, net_profit=65_000)

    assert DECISION_RULES.high_rent_warning in result.warnings


def test_non_positive_profit_adds_warning() -> None:
    negative_result = make_decision(total_score=82, rent=85_000, net_profit=-1)
    zero_result = make_decision(total_score=82, rent=85_000, net_profit=0)

    assert DECISION_RULES.unprofitable_warning in negative_result.warnings
    assert DECISION_RULES.unprofitable_warning in zero_result.warnings


def test_missing_income_adds_informational_warning() -> None:
    result = make_decision(total_score=82, rent=85_000, net_profit=None)

    assert DECISION_RULES.income_missing_warning in result.warnings
