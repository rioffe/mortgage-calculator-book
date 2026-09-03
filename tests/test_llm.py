import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from mortgage_calculator_book.config import HOSTED_MODEL
from mortgage_calculator_book.llm import ask_hosted, ask_local


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


def _hosted_first():
    call = SimpleNamespace(
        id="call_1",
        function=SimpleNamespace(
            name="calculate_mortgage_payment",
            arguments=json.dumps(
                {
                    "principal": 200000,
                    "annual_rate": 0.06,
                    "term_years": 30,
                    "payments_per_year": 12,
                }
            ),
        ),
    )
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="", tool_calls=[call]))]
    )


def _hosted_second(answer: str):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=answer))])


def _install_hosted(monkeypatch, answer: str) -> MagicMock:
    create = MagicMock(side_effect=[_hosted_first(), _hosted_second(answer)])
    monkeypatch.setattr(
        "mortgage_calculator_book.llm._client",
        SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))),
    )
    return create


def test_ask_hosted_calls_tool_and_returns_answer(monkeypatch):
    create = _install_hosted(monkeypatch, "Your payment would be $1,199.10.")

    answer = ask_hosted("What would my payment be on a $200,000, 6%, 30 year loan?")

    assert "1,199.10" in answer
    assert create.call_count == 2  # one tool call + one final answer


def test_ask_hosted_defaults_to_hosted_model(monkeypatch):
    create = _install_hosted(monkeypatch, "ok")

    ask_hosted("hi")

    assert [c.kwargs["model"] for c in create.call_args_list] == [HOSTED_MODEL, HOSTED_MODEL]


def test_ask_hosted_honours_model_override(monkeypatch):
    create = _install_hosted(monkeypatch, "ok")

    ask_hosted("hi", model="meta/llama3")

    assert all(c.kwargs["model"] == "meta/llama3" for c in create.call_args_list)
