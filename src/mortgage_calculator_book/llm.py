import json

import ollama
from openai import OpenAI

from mortgage_calculator_book.config import HOSTED_MODEL, OPENROUTER_API_KEY
from mortgage_calculator_book.tool import call_tool, get_tool_definition

LOCAL_MODEL = "qwen3:8b"

# One OpenAI client, reused across every call — no need to reconnect per question.
_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)


def ask_local(question: str, model: str = LOCAL_MODEL) -> str:
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
        model=model,
        messages=[{"role": "user", "content": question}],
        tools=tools,
    )
    message = first["message"]
    tool_calls = message.get("tool_calls")

    if not tool_calls:
        # The model chose to answer without calling the tool at all.
        return message["content"]

    call = tool_calls[0]
    result = call_tool(call["function"]["arguments"])

    second = ollama.chat(
        model=model,
        messages=[
            {"role": "user", "content": question},
            message,
            {"role": "tool", "content": str(result)},
        ],
    )
    return second["message"]["content"]


def ask_hosted(question: str, model: str = HOSTED_MODEL) -> str:
    # Same tool shape as ask_local — OpenAI's format and Ollama's happen
    # to agree here, which is part of why get_tool_definition() didn't
    # need to change to support a second client.
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
        model=model,
        messages=[{"role": "user", "content": question}],
        tools=tools,
    )
    message = first.choices[0].message

    if not message.tool_calls:
        return message.content

    # Only the first tool call matters, same as ask_local — one tool, one
    # call. Arguments arrive as a JSON string here, not a dict, so they
    # need parsing before call_tool can use them.
    call = message.tool_calls[0]
    arguments = json.loads(call.function.arguments)
    result = call_tool(arguments)

    # Two real differences from ask_local, easy to miss: OpenAI's API
    # requires a tool_call_id on the reply, linking this result back to
    # the specific call that requested it, and it expects the content as
    # an actual JSON string (json.dumps), not Python's str().
    second = _client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": question},
            message,
            {"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)},
        ],
    )
    return second.choices[0].message.content
