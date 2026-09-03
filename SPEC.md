# SPEC.md — Fixed-Rate Mortgage Calculator

## What it does
Calculates the fixed periodic payment for a fixed-rate mortgage,
given a principal amount, an annual interest rate, a loan term in
years, and a payment frequency.

## Inputs
- principal: the loan amount, in dollars
- annual_rate: the annual interest rate, as a decimal (e.g. 0.06 for 6%)
- term_years: the length of the loan, in years
- payments_per_year: number of payments per year (default: 12, monthly)

## Derived quantities
- periodic_rate = annual_rate / payments_per_year
- n_payments = term_years * payments_per_year

## Outputs
- payment: the fixed amount paid each period

## Interfaces
- Command-line interface (human-readable and JSON output)
- Desktop GUI:
  - Inputs: principal, annual rate, term (years), payments per year
  - Actions: Calculate (computes and displays the payment), Clear
    (resets all fields and the result)
  - Invalid input shows an error message in place, not a crash

## What "correct" means
The computed payment, multiplied by n_payments, should equal the
total amount paid over the life of the loan. For principal =
$200,000, annual_rate = 0.06, term_years = 30, payments_per_year =
12: payment should equal $1,199.10 (see docs/derivation.md for the
full derivation).

## Out of scope
- Variable-rate mortgages
- Refinancing calculations
- Multiple currencies
