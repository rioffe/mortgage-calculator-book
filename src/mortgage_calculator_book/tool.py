"""Agent-callable tool surface for the fixed-rate mortgage calculator.

Exposes a JSON-Schema-style tool definition and a ``call_tool`` entry point so
an agent can compute a mortgage payment the same way the CLI and GUI do. The
domain rules live in :mod:`mortgage_calculator_book.validation`, which
:func:`call_tool` reuses so the three surfaces can never disagree.

Per the SPEC ("Invalid input shows an error message in place, not a crash"),
:func:`call_tool` never raises: a bad or missing input yields a dict with an
``error`` message naming the offending field, and a good input yields a dict
with ``payment``.
"""

from pydantic import ValidationError

from mortgage_calculator_book.validation import MortgageInput, calculate_validated_payment

TOOL_NAME = "calculate_mortgage_payment"

TOOL_DESCRIPTION = (
    "Calculate the fixed periodic payment for a fixed-rate mortgage, given "
    "a principal amount, an annual interest rate, a loan term in years, and "
    "how many payments are made per year. Use this whenever the user asks "
    "about a mortgage payment amount for a fixed-rate loan."
)

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "principal": {
            "type": "number",
            "description": "The loan amount, in dollars (must be > 0).",
        },
        "annual_rate": {
            "type": "number",
            "description": (
                "The annual interest rate as a decimal in [0.0, 1.0] (e.g. 0.06 for 6%/yr)."
            ),
        },
        "term_years": {
            "type": "number",
            "description": "The length of the loan, in years (must be > 0; may be fractional).",
        },
        "payments_per_year": {
            "type": "integer",
            "description": "Number of payments per year (must be >= 1; defaults to 12, monthly).",
        },
    },
    "required": ["principal", "annual_rate", "term_years"],
    "additionalProperties": False,
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "payment": {
            "type": "number",
            "description": "The fixed periodic payment, in dollars.",
        }
    },
    "required": ["payment"],
}


def call_tool(params: dict) -> dict:
    """Validate the input and compute the payment, never raising.

    Returns a dict carrying exactly one field: ``"payment"`` on success, or
    ``"error"`` on any problem (a missing field, an out-of-range value, or an
    otherwise malformed call). The shared :class:`MortgageInput` model names the
    offending parameter in the error, matching the SPEC's "error in place, not a
    crash" contract. The ``except Exception`` net is a defensive backstop so a
    malformed call can't escape the tool boundary.
    """
    try:
        data = MortgageInput(**params)
    except ValidationError as exc:
        errors = exc.errors()
        return {"error": errors[0]["msg"] if errors else "Invalid input"}
    except Exception as exc:
        return {"error": str(exc)}

    # Money is rounded to the cent on the way out.
    return {"payment": round(calculate_validated_payment(data), 2)}


def get_tool_definition() -> dict:
    """Return the JSON-Schema-style definition an agent uses to call this tool."""
    return {
        "name": TOOL_NAME,
        "description": TOOL_DESCRIPTION,
        "parameters": INPUT_SCHEMA,
        "output_schema": OUTPUT_SCHEMA,
    }
