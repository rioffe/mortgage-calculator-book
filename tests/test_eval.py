# tests/test_eval.py
from mortgage_calculator_book.eval import score_case


def _fake_ask_correct(question: str) -> dict:
    return {
        "answer": "It would be $1,199.10.",
        "tool_called": True,
        "arguments": {
            "principal": 200000,
            "annual_rate": 0.06,
            "term_years": 30,
            "payments_per_year": 12,
        },
    }


def _fake_ask_no_call(question: str) -> dict:
    return {"answer": "I'm not sure.", "tool_called": False, "arguments": None}


def test_score_case_passes_on_matching_call():
    case = {
        "id": "basic-1",
        "question": "irrelevant here",
        "expected_tool_call": True,
        "expected_arguments": {"principal": 200000, "annual_rate": 0.06, "term_years": 30},
    }
    assert score_case(case, _fake_ask_correct)["passed"] is True


def test_score_case_fails_when_tool_not_called_but_expected():
    case = {"id": "basic-1", "question": "irrelevant here", "expected_tool_call": True}
    assert score_case(case, _fake_ask_no_call)["passed"] is False
