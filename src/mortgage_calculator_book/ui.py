"""PyQt5 desktop GUI for the fixed-rate mortgage calculator.

Built strictly from the "Desktop GUI" section of SPEC.md:

    inputs:    principal, annual rate, term (years), payments per year
    actions:   Calculate (computes + displays the payment),
               Clear   (resets all fields and the result)
    errors:    invalid input shows an error message in place, not a crash

The presentation layer is deliberately thin: all parsing, validation and
computation live in :func:`interpret_entries`, a pure function with no Qt
dependency, so the behaviour is exercisable without a Qt event loop. The
widget only reads the fields, calls that function, and lays out the result.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from pydantic import ValidationError
from PyQt5 import QtWidgets

from mortgage_calculator_book.validation import MortgageInput, calculate_validated_payment

# Default payment frequency, per SPEC.md ("payments_per_year default: 12").
PAYMENTS_PER_YEAR_DEFAULT = 12


@dataclass
class Interpretation:
    """Outcome of interpreting the four field values.

    Exactly one of ``payment`` / ``error`` is set: a successful parse,
    validate and compute sets ``payment``; any problem sets ``error`` to a
    human-readable message that names the offending field.
    """

    payment: float | None
    error: str | None

    @property
    def ok(self) -> bool:
        return self.error is None


def format_payment(payment: float) -> str:
    """Format a computed payment for display, e.g. ``Fixed periodic payment: $1,199.10``."""
    return f"Fixed periodic payment: ${payment:,.2f}"


def _parse_float(text: str, name: str) -> float:
    """Parse ``text`` as a float, naming the offending field on failure."""
    stripped = text.strip()
    if not stripped:
        raise ValueError(f"{name} is required")
    try:
        return float(stripped)
    except ValueError:
        raise ValueError(f"{name} must be a number, got {text!r}") from None


def interpret_entries(
    principal_text: str,
    annual_rate_text: str,
    term_years_text: str,
    payments_per_year_text: str,
) -> Interpretation:
    """Parse the four field values, validate them, and compute the payment.

    Returns an :class:`Interpretation` carrying either a ``payment`` (on
    success) or an ``error`` message naming the offending field. No exception
    escapes: every failure is reported in place, matching the SPEC's
    "Invalid input shows an error message in place, not a crash".
    """
    # 1. Parse the free-text fields. A blank or non-numeric entry is itself an
    #    in-place error, so try each one and name the field that broke.
    try:
        principal = _parse_float(principal_text, "principal")
        annual_rate = _parse_float(annual_rate_text, "annual_rate")
        term_years = _parse_float(term_years_text, "term_years")
    except ValueError as exc:
        return Interpretation(payment=None, error=str(exc))

    # payments_per_year is a whole count; the spin box hands us "12"-style text.
    parsed_ppy = payments_per_year_text.strip()
    if not parsed_ppy:
        return Interpretation(payment=None, error="payments_per_year is required")
    try:
        payments_per_year = int(parsed_ppy)
    except ValueError:
        return Interpretation(
            payment=None,
            error=f"payments_per_year must be a whole number, got {payments_per_year_text!r}",
        )

    # 2. Domain validation, reusing the exact model the CLI validates against
    #    so the two surfaces can never disagree.
    try:
        data = MortgageInput(
            principal=principal,
            annual_rate=annual_rate,
            term_years=term_years,
            payments_per_year=payments_per_year,
        )
    except ValidationError as exc:
        errors = exc.errors()
        return Interpretation(payment=None, error=errors[0]["msg"] if errors else "Invalid input")

    # 3. Compute.
    payment = calculate_validated_payment(data)
    return Interpretation(payment=payment, error=None)


class MortgageCalculatorWidget(QtWidgets.QWidget):
    """The fixed-rate mortgage calculator window.

    Inputs mirror SPEC.md exactly; the result line follows
    docs/ui.md's ``Fixed periodic payment: $1,199.10`` format.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Fixed-Rate Mortgage Calculator")

        # Inputs ----------------------------------------------------------------
        self.principal_field = QtWidgets.QLineEdit()
        self.rate_field = QtWidgets.QLineEdit()
        self.term_field = QtWidgets.QLineEdit()
        self.payments_field = QtWidgets.QSpinBox()
        self.payments_field.setRange(1, 1_000_000)
        self.payments_field.setValue(PAYMENTS_PER_YEAR_DEFAULT)

        # Actions ---------------------------------------------------------------
        self.calculate_button = QtWidgets.QPushButton("Calculate")
        self.calculate_button.setDefault(True)
        self.clear_button = QtWidgets.QPushButton("Clear")

        # Result / status -------------------------------------------------------
        self.result_label = QtWidgets.QLabel("Fixed periodic payment: ")
        self.result_label.setStyleSheet("font-weight: bold;")
        self.error_label = QtWidgets.QLabel("")
        self.error_label.setStyleSheet("color: #b00000;")
        self.error_label.setWordWrap(True)

        # Build the layout -------------------------------------------------------
        self._build_layout()
        self._connect_signals()

    def _build_layout(self) -> None:
        form = QtWidgets.QFormLayout()
        form.addRow("Principal ($):", self.principal_field)
        form.addRow("Annual rate (e.g. 0.06):", self.rate_field)
        form.addRow("Term (years):", self.term_field)
        form.addRow("Payments per year:", self.payments_field)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addWidget(self.calculate_button)
        buttons.addWidget(self.clear_button)
        buttons.addStretch(1)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(buttons)
        layout.addWidget(self.result_label)
        layout.addWidget(self.error_label)
        self.setLayout(layout)

    def _connect_signals(self) -> None:
        self.calculate_button.clicked.connect(self._on_calculate)
        self.clear_button.clicked.connect(self.clear)
        # Pressing Enter in any free-text field triggers a calculation.
        for field in (self.principal_field, self.rate_field, self.term_field):
            field.returnPressed.connect(self._on_calculate)

    def _on_calculate(self) -> None:
        """Signal slot for Calculate (button or Enter): run and refresh, discarding the result."""
        self.calculate()

    def calculate(self) -> Interpretation:
        """Compute the payment from the current fields and refresh the labels.

        On success the result line shows the formatted payment and the error
        line is cleared. On any problem the result line is reset and the error
        message is shown in place -- the window never crashes. Returns the
        :class:`Interpretation` (handy for tests)."""
        interpretation = interpret_entries(
            self.principal_field.text(),
            self.rate_field.text(),
            self.term_field.text(),
            str(self.payments_field.value()),
        )

        if interpretation.ok:
            payment = interpretation.payment
            assert payment is not None, "an ok interpretation always carries a payment"
            self.result_label.setText(format_payment(payment))
            self.error_label.setText("")
        else:
            self.result_label.setText("Fixed periodic payment: ")
            self.error_label.setText(interpretation.error or "")
        return interpretation

    def clear(self) -> None:
        """Reset every input to its default and wipe the result and error."""
        self.principal_field.clear()
        self.rate_field.clear()
        self.term_field.clear()
        self.payments_field.setValue(PAYMENTS_PER_YEAR_DEFAULT)
        self.result_label.setText("Fixed periodic payment: ")
        self.error_label.setText("")

    def result_text(self) -> str:
        """The current text of the result line (handy for tests)."""
        return self.result_label.text()


def build_widget() -> MortgageCalculatorWidget:
    """Construct the calculator widget. A thin helper for embedding / testing."""
    return MortgageCalculatorWidget()


def main(argv: list[str] | None = None) -> int:
    """Launch the desktop GUI. Intended as the ``mortgage-calculator-gui`` entry point."""
    # Reuse an existing QApplication when present (e.g. under a test harness);
    # otherwise start a fresh one from the process arguments.
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    widget = build_widget()
    widget.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
