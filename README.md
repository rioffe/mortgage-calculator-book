# Mortgage Calculator

Calculates the **fixed periodic payment** for a fixed-rate mortgage, given a
principal, an annual interest rate, a loan term in years, and a payment
frequency. Implements the formula from [`docs/derivation.md`](docs/derivation.md):

```text
M = P * [r(1+r)^n] / [(1+r)^n - 1]
```

where `P` is the principal, `r` is the periodic rate (`annual_rate /
payments_per_year`), and `n` is the total number of payments
(`term_years * payments_per_year`).

## The worked example

`$200,000` at `6%` over `30 years`, paid monthly (`12`/yr):

```bash
$ mortgage-calculator-book --principal 200000 --annual-rate 0.06 --term-years 30
Fixed periodic payment: $1,199.10
```

## Install

Uses [uv](https://github.com/astral-sh/uv) and requires Python ≥ 3.12.

```bash
uv sync            # create the .venv and install dependencies
```

## Use it

### Command line

The console script `mortgage-calculator-book` is the entry point
(`mortgage_calculator_book.cli:main`). Run it with `uv run` for a one-off, or
call the script in the venv directly:

```bash
uv run mortgage-calculator-book --principal 200000 --annual-rate 0.06 --term-years 30
# Fixed periodic payment: $1,199.10

uv run mortgage-calculator-book --help
```

Common examples:

```bash
# Monthly (12/yr is the default)
uv run mortgage-calculator-book --principal 200000 --annual-rate 0.06 --term-years 30

# Quarterly, as JSON
uv run mortgage-calculator-book --principal 200000 --annual-rate 0.06 \
    --term-years 30 --payments-per-year 4 --format json
# {"payment": 3603.7}

# Invalid input is rejected: the offending parameter is named on stderr, exit code 1
uv run mortgage-calculator-book --principal 200000 --annual-rate 1.5 --term-years 30
# Error: annual_rate must be a decimal in [0.0, 1.0] (0% to 100%/yr), got 1.5
```

> Note: `cli.py` has no `if __name__ == "__main__"` guard, so
> `python -m mortgage_calculator_book.cli` imports the module but runs nothing —
> use the console script above instead.

Options:

| Flag                  | Required | Default | Meaning                                |
| --------------------- | -------- | ------- | -------------------------------------- |
| `--principal`         | yes      | —       | Loan amount, in dollars                |
| `--annual-rate`       | yes      | —       | Annual rate as a decimal (`0.06` = 6%) |
| `--term-years`        | yes      | —       | Loan term, in years                    |
| `--payments-per-year` | no       | `12`    | Payments per year (monthly by default) |
| `--format`            | no       | `text`  | Output format: `text` or `json`        |

### As a library

The core function is pure (no I/O); the validated input model is the supported
entry point:

```python
from mortgage_calculator_book.validation import MortgageInput, calculate_validated_payment

result = calculate_validated_payment(
    MortgageInput(principal=200_000, annual_rate=0.06, term_years=30, payments_per_year=12)
)
print(f"{result:,.2f}")  # 1,199.10

# Or call the raw, unvalidated core directly:
from mortgage_calculator_book.core import calculate_payment

calculate_payment(200_000, 0.06, 30, 12)  # ~1199.10
```

## Inputs & constraints

Validation happens in `MortgageInput` (`validation.py`); each field's
`field_validator` raises a message that names the offending parameter.

| Field               | Valid domain                                |
| ------------------- | ------------------------------------------- |
| `principal`         | `> 0` (a positive dollar amount)            |
| `annual_rate`       | `0.0 ≤ rate ≤ 1.0` (0% to 100%/yr, decimal) |
| `term_years`        | `> 0` (may be fractional)                   |
| `payments_per_year` | `≥ 1` (default `12`)                        |

**Edge cases.** A zero interest rate (`annual_rate == 0.0`) is valid and valid:
the closed form collapses to `0/0`, so the loan is split evenly across all
payments (`principal / n_payments`).

## Project layout

```text
src/mortgage_calculator_book/
 __init__.py                     # package docstring / top-level module
 core.py                         # calculate_payment: the pure formula
 validation.py                   # MortgageInput (pydantic) + calculate_validated_payment entry point
 cli.py                          # argument parsing -> validation -> print (the console script)
tests/                         # pytest: test_core.py, test_validation.py, conftest.py
docs/derivation.md             # the formula and where it comes from
SPEC.md                        # the spec this project is built against
```

`config.py`, `.env.example`, and the `python-dotenv` / `requests` dependencies are
scaffolding for later chapters; they are not wired into the calculator above.

## Testing

```bash
uv run pytest        # 28 tests
uv run ruff check    # lint
```

The reference answer key — `$200,000 / 6% / 30 yr / monthly → $1,199.10` — is the
case every test checks against (see `docs/derivation.md`).

## Out of scope

Variable-rate mortgages, refinancing, and multiple currencies are not supported.
See [`SPEC.md`](SPEC.md) for the full specification.
