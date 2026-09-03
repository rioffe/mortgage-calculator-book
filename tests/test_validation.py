import pytest
from pydantic import ValidationError

from mortgage_calculator_book.validation import MortgageInput


def test_valid_input_accepted():
    result = MortgageInput(principal=200_000, annual_rate=0.06, term_years=30, payments_per_year=12)
    assert result.principal == 200_000


def test_negative_principal_rejected():
    with pytest.raises(ValidationError):
        MortgageInput(principal=-1000, annual_rate=0.06, term_years=30)


def test_zero_principal_rejected():
    with pytest.raises(ValidationError):
        MortgageInput(principal=0, annual_rate=0.06, term_years=30)


def test_zero_rate_accepted():
    """Zero interest is valid (see docs/derivation.md), not an error."""
    result = MortgageInput(principal=12_000, annual_rate=0.0, term_years=1)
    assert result.annual_rate == 0.0


def test_negative_rate_rejected():
    with pytest.raises(ValidationError):
        MortgageInput(principal=200_000, annual_rate=-0.01, term_years=30)


def test_rate_above_one_rejected():
    with pytest.raises(ValidationError):
        MortgageInput(principal=200_000, annual_rate=1.5, term_years=30)


def test_zero_term_rejected():
    with pytest.raises(ValidationError):
        MortgageInput(principal=200_000, annual_rate=0.06, term_years=0)
