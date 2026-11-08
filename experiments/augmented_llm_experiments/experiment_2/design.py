"""Inputs and prompt variants for independent tool-call batch experiments."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from agent.tools.read_file import read_file

START = "<start_tool_call>"
END = "<end_tool_call>"

# The weather tool is a hypothetical schema for mixed-tool selection tests.
TOOLS = [
    read_file.schema,
    {
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
            "additionalProperties": False,
        },
    },
]


def call(tool, **arguments):
    return {"tool": tool, "arguments": arguments}


CASES = [
    {
        "id": "one_file",
        "category": "single",
        "prompt": "Read notes.txt and summarize it.",
        "expected": [call("read_file", path="notes.txt")],
    },
    {
        "id": "code_file",
        "category": "single",
        "prompt": "Read agent/tools/read_file.py and explain its contents.",
        "expected": [call("read_file", path="agent/tools/read_file.py")],
    },
    {
        "id": "two_files",
        "category": "multiple",
        "prompt": "Read README.md and notes.txt and summarize both files.",
        "expected": [
            call("read_file", path="README.md"),
            call("read_file", path="notes.txt"),
        ],
    },
    {
        "id": "three_files",
        "category": "multiple",
        "prompt": "Read README.md, notes.txt, and docs/guide.md. Summarize each file.",
        "expected": [
            call("read_file", path="README.md"),
            call("read_file", path="notes.txt"),
            call("read_file", path="docs/guide.md"),
        ],
    },
    {
        "id": "path_spaces",
        "category": "single",
        "prompt": "Read the file 'docs/release notes.md' and summarize it.",
        "expected": [call("read_file", path="docs/release notes.md")],
    },
    {
        "id": "weather_city",
        "category": "single",
        "prompt": "What is the current weather in Seoul?",
        "expected": [call("get_weather", city="Seoul")],
    },
    {
        "id": "weather_two",
        "category": "multiple",
        "prompt": "What is the current weather in Seoul and Busan?",
        "expected": [
            call("get_weather", city="Seoul"),
            call("get_weather", city="Busan"),
        ],
    },
    {
        "id": "mixed_tools",
        "category": "multiple",
        "prompt": "Read README.md and tell me the current weather in Seoul.",
        "expected": [
            call("read_file", path="README.md"),
            call("get_weather", city="Seoul"),
        ],
    },
    {"id": "greeting", "category": "no_tool", "prompt": "Hello there!", "expected": []},
    {
        "id": "arithmetic",
        "category": "no_tool",
        "prompt": "What is 2 + 3?",
        "expected": [],
    },
    {
        "id": "missing_path",
        "category": "missing_argument",
        "prompt": "Can you read a file for me?",
        "expected": [],
    },
    {
        "id": "missing_city",
        "category": "missing_argument",
        "prompt": "What is the weather right now?",
        "expected": [],
    },
]

FORMATS = ["marked_array", "plain_array", "marked_object", "plain_object"]
STYLES = ["concise", "examples"]


def render_calls(calls, output_format):
    """Render a batch in the chosen experimental format."""

    payload = {"tool_calls": calls} if output_format.endswith("object") else calls
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return f"{START}{text}{END}" if output_format.startswith("marked_") else text


def instruction(style, output_format):
    """Create a prompt with the same rules across the four formats."""

    empty = render_calls([], output_format)
    shape = render_calls([call("read_file", path="example.txt")], output_format)
    rules = (
        "Select all independent tool calls needed for the user's request. "
        "Return only one batch in the required format, with no other text. "
        "Each call has exactly 'tool' and 'arguments'. Use only the listed tool names "
        "and their schemas. Use only arguments provided by the user. "
        "Do not invent paths, cities, or tool results. "
        f"If no tool is needed or a required argument is missing, return {empty}. "
        f"Required format: {shape}.\nAvailable tools: "
        + json.dumps(TOOLS, ensure_ascii=False)
    )
    if style == "examples":
        examples = [
            ("Read draft.md.", [call("read_file", path="draft.md")]),
            (
                "Read east.txt and west.txt.",
                [
                    call("read_file", path="east.txt"),
                    call("read_file", path="west.txt"),
                ],
            ),
            ("Hi!", []),
        ]
        rules += "\nExamples:\n" + "\n".join(
            f"User: {prompt}\nOutput: {render_calls(batch, output_format)}"
            for prompt, batch in examples
        )
    return rules
