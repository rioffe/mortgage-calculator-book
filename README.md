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

The CLI's calculator path — and the GUI's Calculate / Clear — need nothing else. The LLM ask
layer (the `mortgage-ask` command and the GUI's Ask button), though, reads its
`OPENROUTER_API_KEY` from the environment (or an optional `.env`; see `.env.example`)
and uses `HOSTED_MODEL` (from `config.py`) for the hosted backend. Copy `.env.example` to
a `.env` and fill in the key, and for local mode install Ollama and run `ollama pull qwen3:8b`.

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

### Desktop GUI

The console script `mortgage-calculator-gui` opens a [PyQt5](https://www.riverbankcomputing.com/software/pyqt) window with the four inputs, a **Calculate / Clear** row, and an **Ask** row (`mortgage_calculator_book.ui:main`):

```bash
uv run mortgage-calculator-gui
```

It needs a desktop display. Calculate and Clear are a thin shell over the same `calculate_validated_payment` core, so they agree with the CLI, and invalid input shows an error in place, never a crash.
The Ask row sends a typed natural-language question to the local model (`ask_local`, Ollama) through the shared tool and shows the plain-language answer below the fields — so, like `mortgage-ask`, it wants a running Ollama with the model pulled; a failed or unavailable model is reported in the answer area, not a crash. See [`docs/ui.md`](docs/ui.md) for the full layout.

### Ask the model

`mortgage-ask` (`mortgage_calculator_book.llm_cli:main`) chats with a language model that answers a mortgage question by calling the shared `calculate_mortgage_payment` tool (`tool.py`) — the same code the CLI and GUI use. Pass a question as positional arguments for a one-off answer, or omit it for an interactive REPL (type `exit` or `quit` at the `>>>` prompt):

```bash
uv run mortgage-ask "What is my payment on a 200k, 6%, 30 year loan?"
uv run mortgage-ask             # interactive: answer "exit" to stop
```

Two backends, selected by `--hosted`:

* **local** (default) — an [Ollama](https://ollama.com) model on your machine, defaulting to `LOCAL_MODEL` (`qwen3:8b`).
* **hosted** — [OpenRouter](https://openrouter.ai) via the OpenAI SDK, defaulting to `HOSTED_MODEL` from `config.py` (`qwen/qwen3.8-27b`).

```bash
uv run mortgage-ask --hosted "..."            # use the hosted model
uv run mortgage-ask --model my/model "..."     # override the default for either backend
```

`--hosted` needs `OPENROUTER_API_KEY` in the environment (see [Install](#install)); local mode needs a running Ollama with the model pulled (`ollama pull qwen3:8b`). A model failure is reported on stderr: exit code 1 in single-shot mode, and a skipped question that the REPL continues past in interactive mode.

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
 __init__.py        # package docstring
 core.py            # calculate_payment: the pure formula
 validation.py      # MortgageInput (pydantic) + calculate_validated_payment
 config.py          # OPENROUTER_API_KEY + HOSTED_MODEL, loaded from the environment (dotenv)
 tool.py            # the calculate_mortgage_payment tool surface (name + JSON schema + call_tool)
 llm.py             # ask_local (Ollama) and ask_hosted (OpenRouter/OpenAI)
 llm_cli.py         # mortgage-ask: the LLM console script (--hosted / --model)
 cli.py             # mortgage-calculator-book: argument parsing -> validation -> print
 ui.py                # mortgage-calculator-gui: the PyQt5 desktop window (calculate, clear, and Ask)
tests/             # pytest: one file per module (core, validation, tool, llm, llm_cli, ui)
docs/              # derivation.md (the math) and ui.md (the GUI layout)
SPEC.md            # the spec this project is built against
```

`config.py` loads `OPENROUTER_API_KEY` and `HOSTED_MODEL` from the environment (via
`python-dotenv`, so an optional `.env` is picked up automatically). `tool.py` is the
shared calculator surface the LLM layer calls; the calculator core, the GUI, and
`llm.py` all reuse the same `calculate_validated_payment`, so any surface agrees.
`requests` is still an unused dependency.

## Testing

```bash
uv run pytest          # 88 tests
uv run ruff check    # lint
```

The reference answer key — `$200,000 / 6% / 30 yr / monthly → $1,199.10` — is the
case every test checks against (see `docs/derivation.md`).

## Out of scope

Variable-rate mortgages, refinancing, and multiple currencies are not supported.
See [`SPEC.md`](SPEC.md) for the full specification.
