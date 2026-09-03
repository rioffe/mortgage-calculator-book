# Fixed-Rate Mortgage Payment: Derivation

## The formula

    M = P * [r(1+r)^n] / [(1+r)^n - 1]

M is the fixed periodic payment, P is the principal, r is the
periodic rate (annual_rate / payments_per_year), and n is the
total number of payments (term_years * payments_per_year).

## Where it comes from

At the end of the loan, what the lender is owed if nothing were
ever paid -- P(1+r)^n -- must equal what's actually been paid,
each payment M grown at rate r for however many periods remain
after it: P(1+r)^n = M * [(1+r)^n - 1] / r. Solving for M gives
the formula above.

## Edge cases

- Zero interest (r == 0): the formula divides by zero; payment is
  simply P / n.
- A single payment (n == 1): reduces to M = P(1+r), which the
  general formula also produces correctly at n=1.

## Answer key

principal=200000, annual_rate=0.06, term_years=30,
payments_per_year=12 -> payment = $1,199.10. Used throughout
tests/test_core.py as the reference case every implementation is
checked against.
