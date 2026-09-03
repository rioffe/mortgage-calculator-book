"""GUI test suite for the fixed-rate mortgage calculator.

The GUI layer is deliberately thin: all logic lives in the pure
``interpret_entries`` function (no Qt), so the bulk of these tests exercise
that without any event loop. The Qt widget itself is driven headless with
``QT_QPA_PLATFORM=offscreen``.

The reference answer key -- $200,000 / 6% / 30 yr / monthly -> $1,199.10 --
echoes tests/test_core.py so the GUI is checked against the same number.
"""

from __future__ import annotations

import os

import pytest

# Offscreen so the widget can be constructed and driven with no display.
# This must be set before the first QApplication is ever instantiated.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# The pure layer imports no Qt widgets and is testable headlessly.
from mortgage_calculator_book.core import calculate_payment
from mortgage_calculator_book.ui import (
    PAYMENTS_PER_YEAR_DEFAULT,
    Interpretation,
    MortgageCalculatorWidget,
    build_widget,
    format_payment,
    interpret_entries,
)

# ---------------------------------------------------------------------------
# Pure layer: interpret_entries / format_payment / Interpretation
# ---------------------------------------------------------------------------

# The one number every test agrees on (docs/derivation.md answer key).
WORKED = {"principal": "200000", "annual_rate": "0.06", "term_years": "30", "ppe": "12"}


def test_format_payment_thousands_comma_and_cents():
    assert format_payment(1199.1) == "Fixed periodic payment: $1,199.10"


def test_format_payment_rounds_to_cents():
    # 1199.005 rounds up; a large principal still gets a thousands comma.
    assert format_payment(1_234_567.895) == "Fixed periodic payment: $1,234,567.90"


def test_interpret_entries_worked_example_is_ok_and_correct():
    result = interpret_entries(
        WORKED["principal"], WORKED["annual_rate"], WORKED["term_years"], WORKED["ppe"]
    )
    assert result.ok
    assert result.error is None
    assert result.payment == pytest.approx(1199.10, abs=0.01)


@pytest.mark.parametrize(
    "principal, rate, term, ppe, expected",
    [
        (200_000.0, "0.06", "30", "1", 14_529.78),
        (200_000.0, "0.06", "30", "4", 3_603.70),
        (200_000.0, "0.06", "30", "26", 553.17),
    ],
)
def test_interpret_entries_non_monthly_frequencies(principal, rate, term, ppe, expected):
    result = interpret_entries(str(principal), rate, term, ppe)
    assert result.ok
    assert result.payment == pytest.approx(expected, abs=0.01)


def test_interpret_entries_matches_core_directly():
    # The GUI path must agree with the pure formula it wraps.
    result = interpret_entries("123456.78", "0.045", "15.5", "6")
    raw = calculate_payment(123456.78, 0.045, 15.5, 6)
    assert result.ok
    assert result.payment == raw


def test_interpret_entries_zero_rate_is_valid():
    # Zero interest is valid (docs/derivation.md): the loan splits evenly.
    result = interpret_entries("120000", "0.0", "12", "12")
    assert result.ok, result.error
    assert result.payment == pytest.approx(120_000 / 144, abs=0.01)


@pytest.mark.parametrize(
    "principal, rate, term, ppe, expect_substring",
    [
        ("abc", "0.06", "30", "12", "principal must be a number"),
        ("", "0.06", "30", "12", "principal is required"),
        ("200000", "abc", "30", "12", "annual_rate must be a number"),
        ("200000", "0.06", "", "12", "term_years is required"),
        ("200000", "0.06", "30", "", "payments_per_year is required"),
        ("200000", "0.06", "30", "3.5", "payments_per_year must be a whole number"),
        ("200000", "1.5", "30", "12", "annual_rate must be a decimal in [0.0, 1.0]"),
        ("200000", "-0.01", "30", "12", "annual_rate must be a decimal in [0.0, 1.0]"),
        ("0", "0.06", "30", "12", "principal must be a positive"),
        ("-500", "0.06", "30", "12", "principal must be a positive"),
        ("200000", "0.06", "0", "12", "term_years must be a positive"),
        ("200000", "0.06", "30", "0", "payments_per_year must be a positive"),
    ],
)
def test_interpret_entries_reports_invalid_in_place(principal, rate, term, ppe, expect_substring):
    # SPEC: invalid input reports an error naming the field -- never a crash.
    result = interpret_entries(principal, rate, term, ppe)
    assert not result.ok
    assert result.payment is None
    assert result.error is not None
    assert expect_substring in result.error


@pytest.mark.parametrize(
    "principal, rate, term, ppe",
    [
        ("abc", "0.06", "30", "12"),
        ("200000", "abc", "30", "12"),
        ("200000", "0.06", "abc", "12"),
        ("200000", "0.06", "30", "3.5"),
        ("200000", "1.5", "30", "12"),
        ("-1", "", "", "0"),  # every field invalid at once
    ],
)
def test_interpret_entries_never_raises(principal, rate, term, ppe):
    # No exception may escape interpret_entries; it always returns a result.
    result = interpret_entries(principal, rate, term, ppe)
    assert isinstance(result, Interpretation)
    assert result.ok == (result.error is None)


def test_ok_interpretation_always_carries_payment():
    result = interpret_entries("100000", "0.05", "10", "12")
    assert result.ok
    assert result.payment is not None
    # The invariant the widget's assert relies on: ok <=> payment is set.
    assert result.error is None


def test_interpret_entries_ignores_surrounding_whitespace():
    assert interpret_entries(" 200000 ", " 0.06 ", " 30 ", " 12 ").ok


# ---------------------------------------------------------------------------
# Qt widget: headless, driven through build_widget() / calculate() / clear()
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def qapp():
    # A single offscreen QApplication shared across the session.
    from PyQt5 import QtWidgets

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    return app


@pytest.fixture
def widget(qapp) -> MortgageCalculatorWidget:
    # A fresh calculator widget for each test.
    return build_widget()


def test_build_widget_returns_calc_widget(qapp):
    w = build_widget()
    assert isinstance(w, MortgageCalculatorWidget)


def test_widget_defaults(qapp):
    w = build_widget()
    assert w.principal_field.text() == ""
    assert w.rate_field.text() == ""
    assert w.term_field.text() == ""
    assert w.payments_field.value() == PAYMENTS_PER_YEAR_DEFAULT == 12
    assert w.result_text() == "Fixed periodic payment: "  # no $ until computed
    assert w.error_label.text() == ""


def test_widget_calculate_success_sets_result_and_clears_error(qapp):
    w = build_widget()
    w.principal_field.setText(WORKED["principal"])
    w.rate_field.setText(WORKED["annual_rate"])
    w.term_field.setText(WORKED["term_years"])
    # ppe field already defaults to 12

    result = w.calculate()

    assert result.ok
    assert w.result_text() == "Fixed periodic payment: $1,199.10"
    assert w.error_label.text() == ""


def test_widget_calculate_failure_shows_error_in_place(qapp):
    # SPEC: invalid input shows an error message in place, not a crash.
    w = build_widget()
    w.principal_field.setText("abc")
    w.rate_field.setText("0.06")
    w.term_field.setText("30")

    result = w.calculate()  # must not raise

    assert not result.ok
    assert "principal must be a number" in w.error_label.text()
    assert w.result_text() == "Fixed periodic payment: "


def test_widget_calculate_then_success_restores_error_label(qapp):
    w = build_widget()
    w.principal_field.setText("-1")
    assert not w.calculate().ok
    assert w.error_label.text() != ""

    # a subsequent valid compute clears the stale error
    w.principal_field.setText("200000")
    w.rate_field.setText("0.06")
    w.term_field.setText("30")
    assert w.calculate().ok
    assert w.error_label.text() == ""
    assert w.result_text() == "Fixed periodic payment: $1,199.10"


def test_widget_clear_resets_fields_and_wipes_result(qapp):
    w = build_widget()
    w.principal_field.setText("200000")
    w.rate_field.setText("0.06")
    w.term_field.setText("30")
    w.payments_field.setValue(4)
    w.calculate()
    assert w.result_text() != "Fixed periodic payment: "

    w.clear()

    assert w.principal_field.text() == ""
    assert w.rate_field.text() == ""
    assert w.term_field.text() == ""
    assert w.payments_field.value() == PAYMENTS_PER_YEAR_DEFAULT
    assert w.result_text() == "Fixed periodic payment: "
    assert w.error_label.text() == ""


def test_widget_calculate_button_triggers_computation(qapp):
    # The Calculate button's clicked signal runs calculate().
    w = build_widget()
    w.principal_field.setText("100000")
    w.rate_field.setText("0.06")
    w.term_field.setText("10")

    w.calculate_button.click()  # emits clicked -> _on_calculate -> calculate()

    assert w.calculate().ok
    assert w.result_text() == format_payment(calculate_payment(100_000, 0.06, 10, 12))


def test_widget_clear_button_triggers_reset(qapp):
    # The Clear button's clicked signal runs clear().
    w = build_widget()
    w.principal_field.setText("500000")
    w.rate_field.setText("0.05")
    w.term_field.setText("25")
    w.payments_field.setValue(3)

    w.clear_button.click()  # emits clicked -> clear()

    assert w.principal_field.text() == ""
    assert w.payments_field.value() == PAYMENTS_PER_YEAR_DEFAULT
    assert w.result_text() == "Fixed periodic payment: "


def test_widget_enter_triggers_calculation(qapp):
    # Pressing Enter in a free-text field runs calculate().
    w = build_widget()
    w.principal_field.setText(WORKED["principal"])
    w.rate_field.setText(WORKED["annual_rate"])
    w.term_field.setText(WORKED["term_years"])

    w.principal_field.returnPressed.emit()  # Enter -> _on_calculate

    assert w.result_text() == "Fixed periodic payment: $1,199.10"


def test_widget_calculate_with_all_fields_invalid_does_not_crash(qapp):
    # The window stays sane when every field is wrong -- no exception.
    w = build_widget()
    w.principal_field.setText("oops")
    w.rate_field.setText("oops")
    w.term_field.setText("oops")

    result = w.calculate()  # must not raise / abort

    assert not result.ok
    assert w.error_label.text() != ""
    assert w.result_text() == "Fixed periodic payment: "
