import json

import ollama
from openai import OpenAI

from mortgage_calculator_book.config import HOSTED_MODEL, OPENROUTER_API_KEY
from mortgage_calculator_book.tool import call_tool, get_tool_definition

LOCAL_MODEL = "qwen3:8b"

# One OpenAI client, reused across every call — no need to reconnect per question.
_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)


# in llm.py, replacing the body of ask_local:

def ask_local_detailed(question: str) -> dict:
    # Same tool shape as Chapter 11.4.2 — one entry, wrapping
    # get_tool_definition()'s name/description/parameters.
    tool_def = get_tool_definition()
    tools = [
        {
            "type": "function",
            "function": {
                "name": tool_def["name"],
                "description": tool_def["description"],
                "parameters": tool_def["parameters"],
            },
        }
    ]

    first = ollama.chat(
        model=LOCAL_MODEL,
        messages=[{"role": "user", "content": question}],
        tools=tools,
    )
    message = first["message"]
    tool_calls = message.get("tool_calls")

    if not tool_calls:
        return {"answer": message["content"], "tool_called": False, "arguments": None}

    # Only the first call matters — still one tool, same as 11.4.2.
    call = tool_calls[0]
    arguments = call["function"]["arguments"]
    result = call_tool(arguments)

    second = ollama.chat(
        model=LOCAL_MODEL,
        messages=[
            {"role": "user", "content": question},
            message,
            {"role": "tool", "content": str(result)},
        ],
    )
    # arguments is returned here too now — the whole reason for this
    # refactor, since scoring needs to see what the model actually sent,
    # not just the final answer.
    return {"answer": second["message"]["content"], "tool_called": True, "arguments": arguments}


def ask_local(question: str) -> str:
    return ask_local_detailed(question)["answer"]

# in llm.py, replacing the body of ask_hosted:

def ask_hosted_detailed(question: str) -> dict:
    tool_def = get_tool_definition()
    tools = [
        {
            "type": "function",
            "function": {
                "name": tool_def["name"],
                "description": tool_def["description"],
                "parameters": tool_def["parameters"],
            },
        }
    ]

    first = _client.chat.completions.create(
        model=HOSTED_MODEL,
        messages=[{"role": "user", "content": question}],
        tools=tools,
    )
    message = first.choices[0].message

    if not message.tool_calls:
        return {
            "answer": message.content,
            "tool_called": False,
            "arguments": None,
        }

    # Same two differences from the local path as 11.6.4 noted: a
    # tool_call_id to thread through, and arguments arriving as a JSON
    # string rather than a dict.
    call = message.tool_calls[0]
    arguments = json.loads(call.function.arguments)
    result = call_tool(arguments)

    second = _client.chat.completions.create(
        model=HOSTED_MODEL,
        messages=[
            {"role": "user", "content": question},
            message,
            {
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result),
            },
        ],
    )
    return {
        "answer": second.choices[0].message.content,
        "tool_called": True,
        "arguments": arguments,
    }


def ask_hosted(question: str) -> str:
    return ask_hosted_detailed(question)["answer"]
