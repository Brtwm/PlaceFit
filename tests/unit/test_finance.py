from app.services.finance import FinanceInput, calculate_finance


def test_default_finance_for_rent_85000_monthly_costs() -> None:
    result = calculate_finance(FinanceInput(rent=85_000))

    assert result.monthly_costs == 295_000


def test_required_gross_income() -> None:
    result = calculate_finance(FinanceInput(rent=85_000))

    assert result.required_gross_income == 375_000


def test_income_360000_net_profit_and_payback() -> None:
    result = calculate_finance(
        FinanceInput(rent=85_000, expected_gross_income_by_user=360_000),
    )

    assert result.net_profit == 65_000
    assert result.payback_months == 9.2


def test_income_none_skips_profit_and_payback() -> None:
    result = calculate_finance(
        FinanceInput(rent=85_000, expected_gross_income_by_user=None),
    )

    assert result.expected_gross_income_by_user is None
    assert result.net_profit is None
    assert result.payback_months is None


def test_income_below_monthly_costs_has_negative_profit_and_no_payback() -> None:
    result = calculate_finance(
        FinanceInput(rent=85_000, expected_gross_income_by_user=200_000),
    )

    assert result.net_profit == -95_000
    assert result.payback_months is None


def test_finance_is_deterministic() -> None:
    input_data = FinanceInput(rent=85_000, expected_gross_income_by_user=360_000)

    assert calculate_finance(input_data) == calculate_finance(input_data)
