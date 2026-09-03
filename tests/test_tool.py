# tests/test_tool.py
import pytest

from mortgage_calculator_book.tool import call_tool, get_tool_definition


def test_valid_call_returns_payment():
    result = call_tool(
        {
            "principal": 200000,
            "annual_rate": 0.06,
            "term_years": 30,
            "payments_per_year": 12,
        }
    )
    assert result["payment"] == pytest.approx(1199.1)
    assert result["payment"] == round(result["payment"], 2)  # money is rounded to the cent


def test_invalid_call_returns_error_dict_not_exception():
    result = call_tool({"principal": -1000, "annual_rate": 0.06, "term_years": 30})
    assert "error" in result


def test_tool_definition_has_name_and_description():
    definition = get_tool_definition()
    assert definition["name"] == "calculate_mortgage_payment"
    assert "mortgage" in definition["description"].lower()
    assert "properties" in definition["parameters"]
