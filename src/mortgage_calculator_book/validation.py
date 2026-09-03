"""Input validation for the fixed-rate mortgage calculator.

The valid domain, per SPEC.md:
- principal: a positive dollar amount (the loan amount, > 0).
- annual_rate: a non-negative rate as a decimal, 0.0 <= rate <= 1.0
  (0.0 is a valid branch, handled specially by the payment formula; a rate
  at or above 100% is out of scope for this calculator).
- term_years: a positive loan term in years (> 0).
- payments_per_year: a positive count of payments per year (default 12, monthly).
"""

from pydantic import BaseModel, Field


class MortgageInput(BaseModel):
    principal: float = Field(gt=0)
    annual_rate: float = Field(ge=0.0, le=1.0)
    term_years: float = Field(gt=0)
    payments_per_year: int = Field(default=12, ge=1)
