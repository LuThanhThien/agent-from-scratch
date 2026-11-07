from functools import wraps
from inspect import Parameter, getdoc, iscoroutinefunction, signature
import json
from typing import get_type_hints

# NOTE: supported annotation types
_JSON_TYPES = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
}


def tool(func):
    """Generate a tool schema and validate arguments before execution."""

    # Check function
    if iscoroutinefunction(func):
        raise TypeError("Tools must be synchronous functions")

    # Build input schema
    func_signature = signature(func)
    type_hints = get_type_hints(func)
    properties = {}
    required = []

    for name, parameter in func_signature.parameters.items():
        if parameter.kind not in (
            Parameter.POSITIONAL_OR_KEYWORD,
            Parameter.KEYWORD_ONLY,
        ):
            raise TypeError("Tools must use named parameters")

        python_type = type_hints.get(name)
        if python_type not in _JSON_TYPES:
            raise TypeError(f"{name}: unsupported type annotation {python_type}")

        properties[name] = {"type": _JSON_TYPES[python_type]}
        if parameter.default is Parameter.empty:
            required.append(name)
        else:
            if type(parameter.default) is not python_type:
                raise TypeError(f"{name}: default does not match its type")
            properties[name]["default"] = parameter.default

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Validate arguments
        inputs = func_signature.bind(*args, **kwargs)
        inputs.apply_defaults()

        for name, value in inputs.arguments.items():
            expected = type_hints[name]
            # Reject bool as int
            if type(value) is not expected:
                raise TypeError(f"{name} must be {expected.__name__}")

        return func(*inputs.args, **inputs.kwargs)

    # Attach schema
    wrapper.schema = {
        "name": func.__name__,
        "description": getdoc(func) or "",
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        },
    }
    return wrapper


def execute_tool(func, arguments):
    """Execute a tool and return a JSON-compatible success or error result."""

    # Execute and serialize
    try:
        result = func(**arguments)
        data = json.loads(json.dumps(result, allow_nan=False))
        return {"ok": True, "data": data}
    except Exception as error:
        # Error result
        return {
            "ok": False,
            "error": {"type": type(error).__name__, "message": str(error)},
        }
