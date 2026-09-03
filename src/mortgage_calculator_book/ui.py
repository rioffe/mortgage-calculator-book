"""PyQt5 GUI for the fixed-rate mortgage calculator.

Builds the window laid out in docs/ui.md: four labeled input fields
(Principal, Annual rate, Term, Payments per year), a Calculate / Clear
button row, and a result label. The window reuses the same validated
entry point as the CLI (validation.MortgageInput +
calculate_validated_payment), so the GUI and CLI agree on what is
"correct" per docs/derivation.md.
"""

import sys

from pydantic import ValidationError
from PyQt5.QtWidgets import (
    QApplication,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from mortgage_calculator_book.validation import MortgageInput, calculate_validated_payment


class MortgageCalculatorWindow(QWidget):
    """The single-screen mortgage calculator GUI from docs/ui.md."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Mortgage Calculator")

        # Inputs, one per docs/ui.md row. Payments-per-year defaults to "12".
        self.principal_input = QLineEdit()
        self.rate_input = QLineEdit()
        self.term_input = QLineEdit()
        self.frequency_input = QLineEdit("12")

        self.result_label = QLabel("")
        self.calculate_button = QPushButton("Calculate")
        self.calculate_button.clicked.connect(self.on_calculate)
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.on_clear)

        form = QFormLayout()
        form.addRow("Principal ($):", self.principal_input)
        form.addRow("Annual rate (e.g. 0.06):", self.rate_input)
        form.addRow("Term (years):", self.term_input)
        form.addRow("Payments per year:", self.frequency_input)

        layout = QVBoxLayout()
        layout.addLayout(form)
        button_row = QHBoxLayout()
        button_row.addWidget(self.calculate_button)
        button_row.addWidget(self.clear_button)
        layout.addLayout(button_row)
        layout.addWidget(self.result_label)
        self.setLayout(layout)

    def on_calculate(self) -> None:
        """Validate the fields and show either a payment or an error."""
        try:
            data = MortgageInput(
                principal=float(self.principal_input.text()),
                annual_rate=float(self.rate_input.text()),
                term_years=int(self.term_input.text()),
                payments_per_year=int(self.frequency_input.text()),
            )
        except ValidationError as exc:
            self.result_label.setText("\n".join(f"Error: {error['msg']}" for error in exc.errors()))
            return
        except ValueError as exc:
            # A field did not parse as a number (empty / non-numeric text).
            self.result_label.setText(f"Error: {exc}")
            return

        payment = calculate_validated_payment(data)
        self.result_label.setText(f"Fixed periodic payment: ${payment:,.2f}")

    def on_clear(self) -> None:
        """Empty the inputs and clear the result label."""
        self.principal_input.clear()
        self.rate_input.clear()
        self.term_input.clear()
        self.frequency_input.setText("12")
        self.result_label.setText("")


def main() -> None:
    app = QApplication(sys.argv)
    window = MortgageCalculatorWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
