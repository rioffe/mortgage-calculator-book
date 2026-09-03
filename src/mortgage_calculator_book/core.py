"""Mortgage payment computation.

Implements the fixed-rate periodic payment from docs/derivation.md:

    M = P * [r(1+r)^n] / [(1+r)^n - 1]

where r is the periodic rate (annual_rate / payments_per_year) and n is the
total number of payments (term_years * payments_per_year). This function is
pure: it performs no I/O and has no side effects.
"""


def calculate_payment(
    principal: float,
    annual_rate: float,
    term_years: float,
    payments_per_year: int = 12,
) -> float:
    """Return the fixed periodic mortgage payment.

    Args:
        principal: the loan amount.
        annual_rate: the annual interest rate as a decimal (e.g. 0.06 for 6%).
        term_years: the length of the loan, in years (may be fractional).
        payments_per_year: number of payments per year; defaults to monthly (12).

    Returns:
        The fixed amount paid each period.
    """
    periodic_rate = annual_rate / payments_per_year
    n_payments = term_years * payments_per_year

    # With zero interest the closed form collapses to 0/0; the loan is simply
    # split evenly across all payments.
    if periodic_rate == 0.0:
        return principal / n_payments

    factor = (1.0 + periodic_rate) ** n_payments
    return principal * periodic_rate * factor / (factor - 1.0)
