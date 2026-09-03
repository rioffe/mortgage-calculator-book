"""GUI tests for the mortgage calculator window.

PyQt5 needs a platform plugin to run; the offscreen plugin renders
widgets with no display, so these tests run headlessly (CI, no monitor).
The offscreen platform must be selected before the first QApplication,
which happens at import time inside ui.py's QApplication(sys.argv) only
when main() runs, so it is safe to set here before the widget fixtures.
"""

import os

import pytest
from PyQt5.QtWidgets import QApplication

from mortgage_calculator_book.ui import MortgageCalculatorWindow


@pytest.fixture(scope="session")
def qapp():
    # A single offscreen QApplication shared by all GUI tests.
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    return app


@pytest.fixture
def window(qapp):
    # A fresh window per test; qapp ensures a QApplication exists first.
    return MortgageCalculatorWindow()


# --- Layout / wiring: the window matches docs/ui.md ---------------------------


def test_window_title(window):
    assert window.windowTitle() == "Mortgage Calculator"


def test_frequency_defaults_to_monthly_text(window):
    assert window.frequency_input.text() == "12"


def test_inputs_start_blank(window):
    # Principal, rate and term are entered by the user; only frequency is preset.
    assert window.principal_input.text() == ""
    assert window.rate_input.text() == ""
    assert window.term_input.text() == ""


def test_calculate_button_is_wired(window):
    # Clicking the button must invoke the handler that shows a result.
    def fake_handler() -> None:
        window.result_label.setText("clicked")

    window.calculate_button.clicked.disconnect()
    window.calculate_button.clicked.connect(fake_handler)
    window.calculate_button.click()
    assert window.result_label.text() == "clicked"


def test_clear_button_is_wired(window):
    window.principal_input.setText("200000")
    window.result_label.setText("stale")

    def fake_handler() -> None:
        window.result_label.setText("cleared")

    window.clear_button.clicked.disconnect()
    window.clear_button.clicked.connect(fake_handler)
    window.clear_button.click()
    assert window.result_label.text() == "cleared"


# --- Calculate: happy path and error reporting -------------------------------


def _enter_inputs(window, principal, rate, term, frequency):
    window.principal_input.setText(principal)
    window.rate_input.setText(rate)
    window.term_input.setText(term)
    window.frequency_input.setText(frequency)


def test_calculate_shows_worked_example(window):
    # The docs/ui.md worked example: $200,000 / 6% / 30yr / monthly.
    _enter_inputs(window, "200000", "0.06", "30", "12")
    window.on_calculate()
    assert window.result_label.text() == "Fixed periodic payment: $1,199.10"


def test_calculation_does_not_mutate_input_fields(window):
    _enter_inputs(window, "200000", "0.06", "30", "12")
    window.on_calculate()
    assert window.principal_input.text() == "200000"


def test_calculate_reports_invalid_rate(window):
    # 1.5 is out of the [0.0, 1.0] domain, so validation rejects it.
    _enter_inputs(window, "200000", "1.5", "30", "12")
    window.on_calculate()
    text = window.result_label.text()
    assert text.startswith("Error:")
    assert "annual_rate" in text


def test_calculate_reports_non_numeric_field(window):
    # Empty principal fails int/float parsing -> a ValueError, one error line.
    _enter_inputs(window, "", "0.06", "30", "12")
    window.on_calculate()
    assert window.result_label.text().startswith("Error:")


# --- Clear -------------------------------------------------------------------


def test_clear_empties_inputs_and_resets_frequency(window):
    _enter_inputs(window, "200000", "0.06", "30", "1")
    window.on_calculate()
    window.on_clear()

    assert window.principal_input.text() == ""
    assert window.rate_input.text() == ""
    assert window.term_input.text() == ""
    assert window.frequency_input.text() == "12"
    assert window.result_label.text() == ""
