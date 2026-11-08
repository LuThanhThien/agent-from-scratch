"""Validate and compare independent tool-call batches without executing tools."""

from collections import Counter
import json
from design import TOOLS

SCHEMAS = {tool["name"]: tool["parameters"] for tool in TOOLS}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate key: {key}")
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError(f"Invalid JSON constant: {value}")


def canonical(calls):
    normalized = []
    for call in calls:
        arguments = dict(call["arguments"])
        if call["tool"] == "read_file" and arguments.get("max_chars") == 10000:
            del arguments["max_chars"]
        normalized.append(
            json.dumps({"tool": call["tool"], "arguments": arguments}, sort_keys=True)
        )
    return Counter(normalized)


def evaluate(response, expected):
    result = {
        "pass": False,
        "format_valid": False,
        "calls_match": False,
        "actual": None,
        "error": None,
    }
    try:
        obj = json.loads(
            response, object_pairs_hook=unique_object, parse_constant=invalid_constant
        )
        if (
            not isinstance(obj, dict)
            or set(obj) != {"tool_calls"}
            or not isinstance(obj["tool_calls"], list)
        ):
            raise ValueError("Expected an object containing only a tool_calls list")
        for item in obj["tool_calls"]:
            if (
                not isinstance(item, dict)
                or set(item) != {"tool", "arguments"}
                or not isinstance(item["tool"], str)
                or not isinstance(item["arguments"], dict)
            ):
                raise ValueError("Each call must contain tool and arguments")
            if item["tool"] not in SCHEMAS:
                raise ValueError("Unknown tool: " + item["tool"])
            schema = SCHEMAS[item["tool"]]
            args = item["arguments"]
            if not set(schema["required"]).issubset(args) or not set(args).issubset(
                schema["properties"]
            ):
                raise ValueError("Missing or extra arguments for " + item["tool"])
            for key, value in args.items():
                kind = schema["properties"][key]["type"]
                if (kind == "string" and not isinstance(value, str)) or (
                    kind == "integer" and type(value) is not int
                ):
                    raise ValueError("Wrong argument type for " + key)
        result["actual"] = obj["tool_calls"]
        result["format_valid"] = True
        result["calls_match"] = canonical(obj["tool_calls"]) == canonical(expected)
        result["pass"] = result["calls_match"]
        if not result["pass"]:
            result["error"] = "Calls differ from expected batch"
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        result["error"] = str(exc)
    return result
