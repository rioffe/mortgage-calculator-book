import json
from pathlib import Path
from typing import Any, Callable

# From eval.py's own location (src/mortgage_calculator_book/), climb three
# levels to the project root, then into data/ -- the same file every eval
# question comes from.
EVAL_SET_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "data" / "eval_set.json"
)


def load_eval_set() -> list[dict[str, Any]]:
    return json.loads(EVAL_SET_PATH.read_text())


def score_case(
    case: dict[str, Any], ask_fn: Callable[[str], dict]
) -> dict[str, Any]:
    # ask_fn is ask_local_detailed or ask_hosted_detailed (12.5.1) --
    # whichever model this run is scoring.
    result = ask_fn(case["question"])

    # First check: did the model call the tool when it should have (or
    # correctly not call it, for an out-of-scope question)? Wrong either
    # way is an automatic fail -- no need to look at arguments at all.
    if result["tool_called"] != case["expected_tool_call"]:
        return {
            "id": case["id"],
            "passed": False,
            "reason": "tool_called mismatch",
        }

    # Second check, only when a call was actually expected: does each
    # argument this case cares about match what the model actually sent?
    # Comparing as floats with a small tolerance avoids false failures
    # from harmless formatting differences like "12" vs "12.0".
    if case["expected_tool_call"] and "expected_arguments" in case:
        for key, expected in case["expected_arguments"].items():
            # arguments is None when no call happened; "or {}" keeps
            # .get() from raising in that case instead of masking it.
            actual = (result["arguments"] or {}).get(key)
            if (
                actual is None
                or abs(float(actual) - float(expected)) > 0.001
            ):
                return {
                    "id": case["id"],
                    "passed": False,
                    "reason": f"argument mismatch: {key}",
                }

    return {"id": case["id"], "passed": True, "reason": None}


def run_eval(
    ask_fn: Callable[[str], dict], verbose: bool = True
) -> list[dict[str, Any]]:
    # One case at a time, not a list comprehension, so progress can be
    # reported as each one finishes -- worth having, given how long a
    # real run over real models actually takes (12.6.1).
    cases = load_eval_set()
    results = []
    for i, case in enumerate(cases, start=1):
        result = score_case(case, ask_fn)
        if verbose:
            status = "PASS" if result["passed"] else "FAIL"
            print(f"[{i}/{len(cases)}] {case['id']}: {status}")
        results.append(result)
    return results


def summarize(results: list[dict[str, Any]]) -> str:
    passed = sum(1 for r in results if r["passed"])
    return f"{passed}/{len(results)} passed"
