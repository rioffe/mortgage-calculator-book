# SPEC.md - Fixed-Rate Mortgage Calculator

## What it does
Calculates the fixed periodic payment for a fixed-rate mortgage,
given a principal amount, an interest rate, and a loan term.

## Inputs
- principal: the loan amount, in dollars
- rate: the interest rate
- term: the length of the loan, in years

## Outputs
- payment: the fixed amount paid each period

## What "correct" means
The computed payment, multiplied by the number of payments,
should equal the total amount paid over the life of the loan.

## Out of scope
- Variable-rate mortgages
- Refinancing calculations
- Multiple currencies
