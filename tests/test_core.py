import pytest
from mortgage_calculator_book.core import calculate_payment


def test_matches_worked_example(worked_example):
    payment = calculate_payment(
        principal=worked_example["principal"],
        annual_rate=worked_example["annual_rate"],
        term_years=worked_example["term_years"],
        payments_per_year=worked_example["payments_per_year"],
    )
    assert payment == pytest.approx(worked_example["expected_payment"], abs=0.01)


# 1. The annual_rate = 0 branch: the standard closed form divides by
#    ((1+r)**n - 1), which collapses to 0/0 at a zero rate, so the
#    implementation must special-case it to principal / n_payments.
def test_zero_interest_rate_splits_principal_evenly():
    # 120_000 over 12 yrs * 12/mo = 144 payments.
    payment = calculate_payment(
        principal=120_000, annual_rate=0.0, term_years=12, payments_per_year=12
    )
    assert payment == pytest.approx(120_000 / 144, abs=0.01)


def test_zero_interest_short_term():
    # default payments_per_year = 12 -> 120_000 over 72 payments.
    payment = calculate_payment(principal=120_000, annual_rate=0.0, term_years=6)
    assert payment == pytest.approx(120_000 / 72, abs=0.01)


# 2. payments_per_year is actually used in both derived quantities
#    (periodic_rate and n_payments), not hardcoded to 12. Every input is
#    carried in the table so each row is self-consistent.
@pytest.mark.parametrize(
    "principal, annual_rate, term_years, payments_per_year, expected",
    [
        (200_000, 0.06, 30, 1, 14_529.78),  # annual (one payment a year)
        (200_000, 0.06, 30, 4, 3_603.70),  # quarterly
        (200_000, 0.06, 30, 12, 1_199.10),  # monthly (== worked example)
        (200_000, 0.06, 30, 26, 553.17),  # biweekly
        (200_000, 0.06, 30, 52, 276.53),  # weekly
    ],
)
def test_non_monthly_frequencies(principal, annual_rate, term_years, payments_per_year, expected):
    payment = calculate_payment(
        principal=principal,
        annual_rate=annual_rate,
        term_years=term_years,
        payments_per_year=payments_per_year,
    )
    assert payment == pytest.approx(expected, abs=0.01)


# 3. payments_per_year defaults to 12. The worked example passes 12
#    explicitly, so it does not exercise the default.
def test_payment_frequency_defaults_to_monthly():
    explicit = calculate_payment(
        principal=200_000, annual_rate=0.06, term_years=30, payments_per_year=12
    )
    default = calculate_payment(principal=200_000, annual_rate=0.06, term_years=30)
    assert default == pytest.approx(explicit, abs=0.0001)


# 4. Fractional / non-integer term_years: n_payments must tolerate a float.
def test_fractional_term_years():
    # 0.5 yr * 12/mo = 6 periods.
    payment = calculate_payment(
        principal=60_000, annual_rate=0.04, term_years=0.5, payments_per_year=12
    )
    assert payment == pytest.approx(10_116.99, abs=0.01)


# 5. Zero principal is degenerate but valid: payment must be 0, not a
#    NaN / zero-division artifact.
def test_zero_principal_yields_zero_payment():
    payment = calculate_payment(principal=0, annual_rate=0.05, term_years=10)
    assert payment == pytest.approx(0.0, abs=0.01)


# 6. Numeric robustness for a near-zero but nonzero rate. A naive closed
#    form suffers cancellation here; this guards the special-case boundary.
def test_near_zero_rate_does_not_divide_by_zero():
    payment = calculate_payment(principal=200_000, annual_rate=0.0006, term_years=30)  # 0.06%/yr
    assert payment == pytest.approx(560.58, abs=0.01)
    assert payment < calculate_payment(principal=200_000, annual_rate=0.06, term_years=30)


# 7. Total-paid round-trip: the SPEC's own definition of "correct" -- the
#    present value of all payments must equal the principal. This catches
#    sign/exponent errors a single spot value would miss.
def test_payments_discount_to_principal():
    principal, rate, term, ppy = 200_000, 0.06, 30, 12
    p = calculate_payment(principal, rate, term, ppy)
    r = rate / ppy
    n = term * ppy
    present_value = sum(p / (1 + r) ** k for k in range(1, n + 1))
    assert present_value == pytest.approx(principal, rel=1e-6)


def test_interest_added_when_rate_positive():
    p = calculate_payment(200_000, 0.06, 30, 12)
    assert p * 360 > 200_000  # total paid strictly exceeds principal


# 8. Linearity: payment is linear in principal.
@pytest.mark.parametrize("scale", [0.5, 2.0, 3.0])
def test_linear_in_principal(scale):
    base = calculate_payment(100_000, 0.06, 30, 12)
    scaled = calculate_payment(100_000 * scale, 0.06, 30, 12)
    assert scaled == pytest.approx(base * scale, rel=1e-9)


# 9. Monotonicity: longer term => smaller payment; higher rate => larger.
def test_longer_term_reduces_payment():
    short = calculate_payment(200_000, 0.06, 10, 12)
    long_term = calculate_payment(200_000, 0.06, 30, 12)
    assert short > long_term


def test_higher_rate_increases_payment():
    low = calculate_payment(200_000, 0.03, 30, 12)
    high = calculate_payment(200_000, 0.12, 30, 12)
    assert high > low


def test_zero_interest_loan():
    payment = calculate_payment(
        principal=12_000,
        annual_rate=0.0,
        term_years=1,
        payments_per_year=12,
    )
    assert payment == pytest.approx(1000.00, abs=0.01)


def test_single_payment():
    payment = calculate_payment(
        principal=10_000,
        annual_rate=0.06,
        term_years=1,
        payments_per_year=1,
    )
    assert payment == pytest.approx(10600.00, abs=0.01)
