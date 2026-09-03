# tests/test_llm_cli.py
from unittest.mock import MagicMock

from mortgage_calculator_book.llm_cli import build_parser, main


def _tool_call_response() -> dict:
    """First turn: the model decides to call the calculator tool."""
    return {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
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
            ],
        }
    }


def _final_response(content: str) -> dict:
    """Final turn: the model returns the written answer."""
    return {"message": {"role": "assistant", "content": content}}


def _q_side_effect(answer: str) -> list[dict]:
    """Two chat() responses for one question that goes through the tool."""
    return [_tool_call_response(), _final_response(answer)]


def _raising_input(lines):
    """Return an input() stand-in that yields lines then raises EOFError."""
    iterator = iter(lines)

    def _input(prompt: str = "") -> str:
        try:
            return next(iterator)
        except StopIteration:
            raise EOFError

    return _input


def fake_input(lines: list[str], monkeypatch):
    monkeypatch.setattr("builtins.input", _raising_input(lines))


def patch_chat(mock, monkeypatch):
    monkeypatch.setattr("mortgage_calculator_book.llm.ollama.chat", mock)


def test_single_shot_prints_answer(monkeypatch, capsys):
    mock = MagicMock(side_effect=_q_side_effect("Your payment would be $1,199.10."))
    patch_chat(mock, monkeypatch)

    code = main(["what", "is", "my", "payment", "on", "a", "200k", "loan"])

    assert code == 0
    assert "1,199.10" in capsys.readouterr().out
    assert mock.call_count == 2  # one tool call + one final answer


def test_single_shot_passes_model_override(monkeypatch):
    mock = MagicMock(side_effect=_q_side_effect("ok"))
    patch_chat(mock, monkeypatch)

    main(["hi", "--model", "llama3.2"])

    assert all(call.kwargs["model"] == "llama3.2" for call in mock.call_args_list)


def test_default_model_is_module_constant(monkeypatch):
    mock = MagicMock(side_effect=_q_side_effect("ok"))
    patch_chat(mock, monkeypatch)

    main(["hi"])

    assert all(call.kwargs["model"] == "qwen3:8b" for call in mock.call_args_list)


def test_repl_runs_questions_then_stops_at_exit(monkeypatch, capsys):
    mock = MagicMock(
        side_effect=(_q_side_effect("Answer 1: $1,199.10.") + _q_side_effect("Answer 2: $2,500.00"))
    )
    patch_chat(mock, monkeypatch)
    fake_input(["first question", "exit", "never asked"], monkeypatch)

    code = main([])

    out = capsys.readouterr().out
    assert code == 0
    assert "Answer 1" in out
    assert "Answer 2" not in out  # the question after "exit" was never processed
    assert mock.call_count == 2  # only "first question" reached the model


def test_single_shot_error_returns_nonzero(monkeypatch, capsys):
    mock = MagicMock(side_effect=ConnectionError("ollama server is not running"))
    patch_chat(mock, monkeypatch)

    code = main(["hi there"])

    err = capsys.readouterr().err
    assert code == 1
    assert "could not reach the model" in err
    assert "ConnectionError" in err


def test_repl_survives_a_failed_question(monkeypatch, capsys):
    mock = MagicMock(side_effect=ConnectionError("down"))
    patch_chat(mock, monkeypatch)
    fake_input(["bad question", "exit"], monkeypatch)

    code = main([])

    out, err = capsys.readouterr()
    assert code == 0  # the session continued instead of crashing
    assert out == ""  # a failed question prints nothing on success
    assert "could not reach the model" in err


def test_parser_defaults():
    parser = build_parser()
    # No positional args -> empty question list (triggers the REPL).
    assert parser.parse_args([]).question == []
    # The default model comes from the module constant.
    assert parser.parse_args(["hi"]).model == "qwen3:8b"
    # A --model override is honoured; separate tokens are collected separately.
    args = parser.parse_args(["--model", "llama3.2", "ask", "me"])
    assert args.model == "llama3.2"
    assert args.question == ["ask", "me"]
