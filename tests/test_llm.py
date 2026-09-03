# tests/test_llm.py
from unittest.mock import MagicMock

from mortgage_calculator_book.llm import ask_local


def test_ask_local_calls_tool_and_returns_answer(monkeypatch):
    tool_call = {
        "function": {
            "name": "calculate_mortgage_payment",
            "arguments": {
                "principal": 200000,
                "annual_rate": 0.06,
                "term_years": 30,
                "payments_per_year": 12,
            },
        }
    }
    first_response = {"message": {"role": "assistant", "content": "", "tool_calls": [tool_call]}}
    second_response = {
        "message": {"role": "assistant", "content": "Your payment would be $1,199.10."}
    }

    mock_chat = MagicMock(side_effect=[first_response, second_response])
    monkeypatch.setattr("mortgage_calculator_book.llm.ollama.chat", mock_chat)

    answer = ask_local("What would my payment be on a $200,000, 6%, 30 year loan?")

    assert "1,199.10" in answer
    assert mock_chat.call_count == 2
