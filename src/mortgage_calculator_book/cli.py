import argparse
import json
import sys

from pydantic import ValidationError

from mortgage_calculator_book.validation import MortgageInput, calculate_validated_payment


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Calculate the fixed periodic payment for a fixed-rate mortgage."
    )
    parser.add_argument("--principal", type=float, required=True, help="Loan amount, in dollars")
    parser.add_argument(
        "--annual-rate", type=float, required=True, help="Annual interest rate, e.g. 0.06 for 6%%"
    )
    parser.add_argument("--term-years", type=int, required=True, help="Loan term, in years")
    parser.add_argument(
        "--payments-per-year", type=int, default=12, help="Payments per year (default: 12)"
    )
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        data = MortgageInput(
            principal=args.principal,
            annual_rate=args.annual_rate,
            term_years=args.term_years,
            payments_per_year=args.payments_per_year,
        )
    except ValidationError as exc:
        for error in exc.errors():
            print(f"Error: {error['msg']}", file=sys.stderr)
        return 1

    payment = calculate_validated_payment(data)
    if args.format == "json":
        print(json.dumps({"payment": round(payment, 2)}))
    else:
        print(f"Fixed periodic payment: ${payment:,.2f}")
    return 0
