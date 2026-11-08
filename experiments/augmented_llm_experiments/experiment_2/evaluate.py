"""Validate batch syntax and compare independent calls without running tools."""

from collections import Counter
import json

from design import START, END, TOOLS


def _pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"Duplicate field: {key}")
        obj[key] = value
    return obj


def _invalid_number(value):
    raise ValueError(f"Invalid JSON number: {value}")


def parse_batch(response, output_format):
    """Parse exactly one batch and validate tool names and argument schemas."""

    text = response.strip()
    if output_format.startswith("marked_"):
        if not text.startswith(START) or not text.endswith(END):
            raise ValueError(
                "Expected opening and closing markers with no surrounding text"
            )
        text = text[len(START) : -len(END)].strip()
    batch = json.loads(text, object_pairs_hook=_pairs, parse_constant=_invalid_number)
    if output_format.endswith("object"):
        if not isinstance(batch, dict) or set(batch) != {"tool_calls"}:
            raise ValueError("Expected an object containing only tool_calls")
        batch = batch["tool_calls"]
    if not isinstance(batch, list):
        raise ValueError("Expected a list of tool calls")
    schemas = {item["name"]: item["parameters"] for item in TOOLS}
    normalized = []
    for item in batch:
        if not isinstance(item, dict) or set(item) != {"tool", "arguments"}:
            raise ValueError("Each call must contain only tool and arguments")
        name = item["tool"]
        if not isinstance(name, str) or name not in schemas:
            raise ValueError(f"Unknown tool: {name!r}")
        args = item["arguments"]
        if not isinstance(args, dict):
            raise ValueError("Tool arguments must be an object")
        schema = schemas[name]
        properties = schema["properties"]
        if not set(args) <= set(properties) or not set(schema["required"]) <= set(args):
            raise ValueError("Unexpected or missing arguments")
        for key, value in args.items():
            expected_type = {"string": str, "integer": int}[properties[key]["type"]]
            if type(value) is not expected_type:
                raise ValueError(f"Invalid argument type for {key}")
        # Supplying the declared default is equivalent to omitting it.
        clean = {
            key: value
            for key, value in args.items()
            if properties[key].get("default", object()) != value
        }
        normalized.append({"tool": name, "arguments": clean})
    return normalized


def evaluate(response, output_format, expected):
    """Check exact format and the order-independent multiset of calls."""

    try:
        actual = parse_batch(response, output_format)
    except (ValueError, TypeError) as error:
        return {
            "pass": False,
            "format_valid": False,
            "calls_match": False,
            "actual": None,
            "error": str(error),
        }
    canonical = lambda calls: Counter(
        json.dumps(c, sort_keys=True, ensure_ascii=False) for c in calls
    )
    matches = canonical(actual) == canonical(expected)
    return {
        "pass": matches,
        "format_valid": True,
        "calls_match": matches,
        "actual": actual,
        "error": None if matches else "Missing, extra, or incorrect calls",
    }
