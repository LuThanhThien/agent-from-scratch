"""Define the fixed cases and prompt variations for the tool-decision experiment."""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREVIOUS = json.loads((HERE.parent / "experiment_2/data/refinement.json").read_text())
TOOLS = PREVIOUS["tools"] + [
    {
        "name": "write_file",
        "description": "Write the provided text to a file at a repository-relative path.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"],
            "additionalProperties": False,
        },
    },
    {
        "name": "open_web",
        "description": "Open a web page at the supplied URL.",
        "parameters": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
            "additionalProperties": False,
        },
    },
]


def call(tool, **arguments):
    return {"tool": tool, "arguments": arguments}


def example(prompt, calls):
    return (
        "User: "
        + prompt
        + "\nOutput: "
        + json.dumps({"tool_calls": calls}, ensure_ascii=False, separators=(",", ":"))
    )


def case(id, category, prompt, expected):
    return {
        "id": id,
        "group": "write_web",
        "category": category,
        "prompt": prompt,
        "expected": expected,
    }


CASES = [{**c, "group": "read_weather"} for c in PREVIOUS["cases"]] + [
    case(
        "write_one",
        "single",
        'Write "Meeting at 9" to notes/meeting.txt.',
        [call("write_file", path="notes/meeting.txt", content="Meeting at 9")],
    ),
    case(
        "write_spaces",
        "single",
        'Write "Ready" to the file "docs/status update.txt".',
        [call("write_file", path="docs/status update.txt", content="Ready")],
    ),
    case(
        "open_one",
        "single",
        "Open https://example.com/docs for me.",
        [call("open_web", url="https://example.com/docs")],
    ),
    case(
        "write_two",
        "multiple",
        'Write "Red" to red.txt and write "Blue" to blue.txt.',
        [
            call("write_file", path="red.txt", content="Red"),
            call("write_file", path="blue.txt", content="Blue"),
        ],
    ),
    case(
        "open_two",
        "multiple",
        "Open both https://example.com/a and https://example.org/b.",
        [
            call("open_web", url="https://example.com/a"),
            call("open_web", url="https://example.org/b"),
        ],
    ),
    case(
        "write_and_open",
        "multiple",
        'Write "Done" to status.txt and open https://example.com/status.',
        [
            call("write_file", path="status.txt", content="Done"),
            call("open_web", url="https://example.com/status"),
        ],
    ),
    case(
        "read_and_write",
        "multiple",
        'Read draft.md, and separately write "Published" to status.txt.',
        [
            call("read_file", path="draft.md"),
            call("write_file", path="status.txt", content="Published"),
        ],
    ),
    case(
        "weather_and_open",
        "multiple",
        "Check the current weather in Paris and open https://example.com/news.",
        [
            call("get_weather", city="Paris"),
            call("open_web", url="https://example.com/news"),
        ],
    ),
    case("second_greeting", "no_tool", "Good morning!", []),
    case(
        "write_missing_path", "missing_argument", 'Write "Hello" to a file for me.', []
    ),
    case(
        "write_missing_content", "missing_argument", "Write something to notes.txt.", []
    ),
    case("open_missing_url", "missing_argument", "Open a web page for me.", []),
]

old = PREVIOUS["variants"]["refine_balanced_examples_plain_object"]["system"]
old_catalog = json.dumps(PREVIOUS["tools"], ensure_ascii=False)
assert old.count(old_catalog) == 1
base = old.replace(old_catalog, json.dumps(TOOLS, ensure_ascii=False))
rules, old_examples = base.split("\nExamples:\n", 1)
old_lines = old_examples.split("\n")
assert len(old_lines) == 12
catalog = "Available tools: " + json.dumps(TOOLS, ensure_ascii=False)


def examples(items, note=""):
    return "\nExamples:\n" + note + "\n".join(example(q, c) for q, c in items)


unrelated = [
    ("Reverse abc.", [call("reverse_text", text="abc")]),
    ("Count letters in hello.", [call("count_letters", text="hello")]),
    (
        "Convert 2 meters to centimeters.",
        [call("convert_units", value="2", unit="meters")],
    ),
    ("Reverse a word for me.", []),
    ("Hello!", []),
    ("What is 4 + 4?", []),
]
abstract = [
    ("Perform action alpha on A.", [call("tool_alpha", arg="A")]),
    ("Perform action beta on B.", [call("tool_beta", arg="B")]),
    (
        "Perform alpha on A and beta on B.",
        [call("tool_alpha", arg="A"), call("tool_beta", arg="B")],
    ),
    ("Perform alpha.", []),
    ("Hello!", []),
    ("What is 4 + 4?", []),
]
all_tools = [
    ("Read memo.md.", [call("read_file", path="memo.md")]),
    ("Check weather in Lima.", [call("get_weather", city="Lima")]),
    ('Write "OK" to memo.md.', [call("write_file", path="memo.md", content="OK")]),
    (
        "Open https://example.net/start.",
        [call("open_web", url="https://example.net/start")],
    ),
    (
        "Read memo.md and open https://example.net/start.",
        [
            call("read_file", path="memo.md"),
            call("open_web", url="https://example.net/start"),
        ],
    ),
    ("Hello!", []),
]
new_tools = [
    ('Write "OK" to memo.md.', [call("write_file", path="memo.md", content="OK")]),
    (
        "Open https://example.net/start.",
        [call("open_web", url="https://example.net/start")],
    ),
    (
        'Write "A" to a.txt and "B" to b.txt.',
        [
            call("write_file", path="a.txt", content="A"),
            call("write_file", path="b.txt", content="B"),
        ],
    ),
    (
        "Open https://example.net/a and https://example.net/b.",
        [
            call("open_web", url="https://example.net/a"),
            call("open_web", url="https://example.net/b"),
        ],
    ),
    ("Write something to memo.md.", []),
    ("Hello!", []),
]
contrast = [
    ("Read memo.md.", [call("read_file", path="memo.md")]),
    ('Write "OK" to memo.md.', [call("write_file", path="memo.md", content="OK")]),
    (
        "Open https://example.net/start.",
        [call("open_web", url="https://example.net/start")],
    ),
    ("Open a web page.", []),
    ("Check weather in Lima.", [call("get_weather", city="Lima")]),
    ("Hello!", []),
]
note = "These examples show format only; their tools are unavailable. Use only the listed tools.\n"
VARIANTS = {
    "baseline_six_examples": (
        "Experiment 2 baseline; catalog expanded to four tools",
        base,
    ),
    "no_task_examples": ("Baseline rules without task examples", rules),
    "no_json_examples": (
        "Describe the JSON structure in prose, no JSON examples",
        "Select all independent requested operations using only the available tools and arguments provided by the user. Never invent arguments. Return only a JSON object with one key named tool_calls containing a list of calls. Each call is an object with a tool string and an arguments object. Use an empty list if no calls can be made.\n"
        + catalog,
    ),
    "old_positive_only": (
        "Baseline with only positive read/weather examples",
        rules + "\nExamples:\n" + "\n".join(old_lines[:6]),
    ),
    "old_negative_only": (
        "Baseline with only no-call examples",
        rules + "\nExamples:\n" + "\n".join(old_lines[6:]),
    ),
    "unrelated_examples": (
        "Examples use other realistic, unavailable tools",
        rules + examples(unrelated, note),
    ),
    "abstract_examples": (
        "Examples use abstract, unavailable tool names",
        rules + examples(abstract, note),
    ),
    "all_tool_examples": (
        "Examples cover all four available tools",
        rules + examples(all_tools),
    ),
    "new_tool_examples": (
        "Examples cover write and web but not read or weather",
        rules + examples(new_tools),
    ),
    "read_write_contrast": (
        "Examples contrast reading and writing and cover all tools",
        rules + examples(contrast),
    ),
    "catalog_last": (
        "Baseline examples precede the tool catalog",
        rules.rsplit("\nAvailable tools: ", 1)[0]
        + "\nExamples:\n"
        + old_examples
        + "\n"
        + catalog,
    ),
    "short_no_examples": (
        "Short instruction without task examples",
        "Select all independent requested tool calls. Use only listed tools and supplied arguments. If required arguments are missing, omit that call. Return only a JSON object with a tool_calls list of objects containing tool and arguments; use an empty list when no calls apply.\n"
        + catalog,
    ),
    "checklist_no_examples": (
        "Baseline rules with a generic coverage checklist",
        rules
        + "\nBefore returning, check every requested independent operation, required arguments, and whether any call was added without a request.",
    ),
    "tool_hints_no_examples": (
        "Baseline rules plus descriptions distinguishing similar tools",
        rules
        + "\nReading does not write. Writing needs a path and exact content. Opening a page needs its URL. Current weather needs a city. Do not infer missing values.",
    ),
}
DESIGN = {
    "model": "meta-llama/Llama-3.2-3B-Instruct",
    "quantization": "4-bit NF4, float16 compute",
    "temperature": 0,
    "max_new_tokens": 160,
    "tools": TOOLS,
    "cases": CASES,
    "variants": {k: {"description": v[0], "system": v[1]} for k, v in VARIANTS.items()},
    "note": "All cases and schemas are fixed across variants. Calls are simulated and never executed. Baseline expands experiment 2 from two tools to four. Original cases are reused, so this is exploratory.",
}

if __name__ == "__main__":
    (HERE / "data/design.json").write_text(
        json.dumps(DESIGN, indent=2, ensure_ascii=False) + "\n"
    )
