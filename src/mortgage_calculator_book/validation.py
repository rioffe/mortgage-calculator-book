"""Input validation for the fixed-rate mortgage calculator.

The valid domain, per SPEC.md:
- principal: a positive dollar amount (the loan amount, > 0).
- annual_rate: a non-negative rate as a decimal, 0.0 <= rate <= 1.0
       (0.0 is a valid branch, handled specially by the payment formula;
        a rate at or above 100% is out of scope for this calculator).
- term_years: a positive loan term in years (> 0).
- payments_per_year: a positive count of payments per year (default 12, monthly).

Design note: the bounds are enforced inside field_validator blocks rather
than via Field(gt=/ge=/le=). A bare Field(gt=0) reports only a generic
"Input should be greater than 0", and in pydantic >= 2.13 a
Field(error_message=...) is a deprecated kwarg pydantic silently ignores.
The validators below instead raise a ValueError that names the offending
parameter, so a rejected value always tells you which one broke.
"""

from pydantic import BaseModel, Field, field_validator

from mortgage_calculator_book.core import calculate_payment


class MortgageInput(BaseModel):
    """Validated mortgage input with per-parameter error messages."""

    principal: float
    annual_rate: float
    term_years: float
    payments_per_year: int = Field(default=12)

    @field_validator("principal")
    @classmethod
    def _check_principal(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"principal must be a positive dollar amount, got {v!r}")
        return v

    @field_validator("annual_rate")
    @classmethod
    def _check_annual_rate(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(
                f"annual_rate must be a decimal in [0.0, 1.0] (0% to 100%/yr), got {v!r}"
            )
        return v

    @field_validator("term_years")
    @classmethod
    def _check_term_years(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"term_years must be a positive number of years (> 0), got {v!r}")
        return v

    @field_validator("payments_per_year")
    @classmethod
    def _check_payments_per_year(cls, v: int) -> int:
        if v < 1:
            raise ValueError(f"payments_per_year must be a positive count (>= 1), got {v!r}")
        return v


def calculate_validated_payment(data: MortgageInput) -> float:
    """The only supported entry point: validated input in, a payment out."""
    return calculate_payment(
        principal=data.principal,
        annual_rate=data.annual_rate,
        term_years=data.term_years,
        payments_per_year=data.payments_per_year,
    )
