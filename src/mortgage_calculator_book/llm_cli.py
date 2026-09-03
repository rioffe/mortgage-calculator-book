"""Command-line harness for the local LLM mortgage calculator.

Wraps :func:`mortgage_calculator_book.llm.ask_local` so a person can chat with
the model from a terminal: the model is offered the shared
``calculate_mortgage_payment`` tool and answers natural-language payment
questions the same way the CLI and GUI do.

Two modes:

* single-shot - the question is given as positional arguments::

      mortgage-ask What is my payment on a 200k, 6%, 30 year loan?

* interactive REPL - with no question, questions are read one per line until
  EOF (Ctrl-D) or ``exit``/``quit``::

      mortgage-ask
      >>> what about 5%?
      >>> exit

A model/ollama failure is reported on stderr with a non-zero exit code in
single-shot mode; in the REPL a failed question is printed to stderr but the
next question is still asked - one bad answer never aborts the session.
"""

import argparse
import sys
from functools import partial

from mortgage_calculator_book.llm import LOCAL_MODEL, ask_local

STOP_COMMANDS = ("exit", "quit")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Ask a natural-language mortgage question to the local LLM, which "
            "computes the answer with the shared calculator tool."
        )
    )
    parser.add_argument(
        "question",
        nargs="*",
        help="The question to ask. Omit it to start an interactive session.",
    )
    parser.add_argument(
        "--model",
        default=LOCAL_MODEL,
        help=f"Ollama model to use (default: {LOCAL_MODEL}).",
    )
    return parser


def _format_error(exc: Exception) -> str:
    return f"Error: could not reach the model ({exc.__class__.__name__}): {exc}"


def run_repl(ask, prompt: str = ">>> ") -> None:
    """Read one question per line from stdin until EOF or exit/quit.

    A question that fails is reported on stderr but the loop continues, so one
    bad answer never aborts the whole session.
    """
    while True:
        try:
            text = input(prompt).strip()
        except EOFError:
            break
        if not text:
            continue
        if text.lower() in STOP_COMMANDS:
            break
        try:
            print(ask(text))
        except Exception as exc:
            print(_format_error(exc), file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    ask = partial(ask_local, model=args.model)

    question = " ".join(args.question).strip()
    if question:
        try:
            print(ask(question))
        except Exception as exc:
            print(_format_error(exc), file=sys.stderr)
            return 1
        return 0

    run_repl(ask)
    return 0


if __name__ == "__main__":
    sys.exit(main())
